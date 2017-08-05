#!/usr/bin/env python2.7


import logging

from babygdcli import (
    get_service, get_file, get_arg_parser, FOLDER_MIME_TYPE,
)


def find(service, path):
    file_id = 'root'
    file_mime_type = FOLDER_MIME_TYPE
    if path:
        components = path.split('/')
        for name in components:
            f = get_file(service, file_id, name)
            file_id = f['id']
            file_mime_type = f['mimeType']
    else:
        path = ''

    print(path if path else '.')

    if file_mime_type == FOLDER_MIME_TYPE:
        queue = [(path, file_id)]

        while queue:
            (parent_path, parent_file_id) = queue.pop()
            response = service.files().list(
                q="'{}' in parents and trashed=false".format(parent_file_id),
            ).execute()
            for f in response.get('files', []):
                name = f['name']
                path = ('/'.join((parent_path, name)) if parent_path else name)
                if f['mimeType'] == FOLDER_MIME_TYPE:
                    queue.insert(0, (path, f['id']))
                print(path)


def main():
    parser = get_arg_parser('list files in a folder, recursively')
    parser.add_argument('path', type=str, nargs='?',
                        help='remote path to list (default: root)')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)-15s %(levelname)s: %(message)s',
        level=logging.INFO,
    )

    service = get_service(args)
    find(service, args.path)


if __name__ == '__main__':
    main()
