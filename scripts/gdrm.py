#!/usr/bin/env python2.7


from __future__ import print_function
import logging

from babygdcli import (
    get_service, get_file, get_arg_parser, FOLDER_MIME_TYPE,
)


def rm_file(service, file_id, path):
    service.files().delete(fileId=file_id).execute()
    logging.info('/dev/null <- {}'.format(path))


def rm(service, path):
    file_id = 'root'
    file_mime_type = FOLDER_MIME_TYPE
    if path != '.' and path != '/' and path != './':
        components = path.split('/')
        for name in components:
            f = get_file(service, file_id, name)
            file_id = f['id']
            file_mime_type = f['mimeType']

    if file_mime_type == FOLDER_MIME_TYPE:
        queue = [(path, file_id)]

        while queue:
            (parent_path, parent_file_id) = queue.pop()
            response = service.files().list(
                q="'{}' in parents and trashed=false".format(parent_file_id),
            ).execute()
            for f in response.get('files', []):
                path = '/'.join((parent_path, f['name']))
                if f['mimeType'] == FOLDER_MIME_TYPE:
                    queue.insert(0, (path, f['id']))
                else:
                    rm_file(service, f['id'], path)

    else:
        rm_file(service, file_id, path)


def main():
    parser = get_arg_parser('remove files or folders')
    parser.add_argument('path', type=str,
                        help='remote path to remove')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)-15s %(levelname)s: %(message)s',
        level=logging.INFO,
    )

    service = get_service(args)
    rm(service, args.path)


if __name__ == '__main__':
    main()
