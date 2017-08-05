#!/usr/bin/env python2.7


from __future__ import print_function
import logging

from babygdcli import (
    get_service, get_file, get_arg_parser, FOLDER_MIME_TYPE,
    set_stdout_encoding,
)


def ls(service, path):
    file_id = 'root'
    file_mime_type = FOLDER_MIME_TYPE
    if path:
        components = path.split('/')
        for name in components:
            f = get_file(service, file_id, name)
            file_id = f['id']
            file_mime_type = f['mimeType']

    if file_mime_type == FOLDER_MIME_TYPE:
        response = service.files().list(
            q="'{}' in parents and trashed=false".format(file_id),
        ).execute()
        for f in response.get('files', []):
            print(f['name'])

    else:
        print(path)


def main():
    parser = get_arg_parser('list files in a folder')
    parser.add_argument('path', type=str, nargs='?',
                        help='remote path to list (default: root)')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)-15s %(levelname)s: %(message)s',
        level=logging.INFO,
    )

    set_stdout_encoding()

    service = get_service(args)
    ls(service, args.path)


if __name__ == '__main__':
    main()
