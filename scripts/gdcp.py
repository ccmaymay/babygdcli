#!/usr/bin/env python2.7


import logging

from apiclient.http import MediaFileUpload, MediaIoBaseDownload

from babygdcli import (
    get_service, get_file_id, NoSuchFile, get_arg_parser, FOLDER_MIME_TYPE,
)


def pull(service, src_path, dst_path, recursive=False):
    if recursive:
        raise Exception('recursive pull not yet implemented')

    file_id = 'root'
    src_components = src_path.split('/')
    for name in src_components:
        file_id = get_file_id(service, file_id, name)

    request = service.files().get_media(fileId=file_id)
    with open(dst_path, 'w') as f:
        downloader = MediaIoBaseDownload(f, request)
        (status, done) = downloader.next_chunk()
        while done is False:
            logging.info('downloading... {:.2f}%'.format(
                status.progress() * 100))
            (status, done) = downloader.next_chunk()

    logging.info('{} <- {}'.format(dst_path, src_path))


def push(service, src_path, dst_path, recursive=False):
    if recursive:
        raise Exception('recursive push not yet implemented')

    file_id = 'root'
    dst_components = dst_path.split('/')
    for name in dst_components[:-1]:
        try:
            new_file_id = get_file_id(service, file_id, name)
        except NoSuchFile:
            response = service.files().create(
                body=dict(
                    name=name,
                    parents=dict(id=file_id),
                    mimeType=FOLDER_MIME_TYPE,
                ),
                fields='id',
            ).execute()
            file_id = response.get('id')
        else:
            file_id = new_file_id

    name = dst_components[-1]
    try:
        new_file_id = get_file_id(service, file_id, name)
    except NoSuchFile:
        request = service.files().create(
            body=dict(
                name=name,
                parents=dict(id=file_id),
            ),
            media_body=MediaFileUpload(src_path, resumable=True),
            fields='id',
        )
    else:
        file_id = new_file_id
        request = service.files().update(
            fileId=file_id,
            media_body=MediaFileUpload(src_path, resumable=True),
        )
    (status, response) = request.next_chunk()
    while response is None:
        logging.info('uploading... {:.2f}%'.format(
            status.progress() * 100))
        (status, response) = request.next_chunk()

    logging.info('{} -> {}'.format(src_path, dst_path))


def main():
    parser = get_arg_parser('pull/push individual files')
    parser.add_argument('command', type=str, choices=('pull', 'push'),
                        help='command to execute against server')
    parser.add_argument('src_path', type=str,
                        help='local/remote path to push/pull, respectively')
    parser.add_argument('dst_path', type=str,
                        help='remote/local path to push/pull to, respectively')
    parser.add_argument('-r', action='store_true',
                        help='recursive')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)-15s %(levelname)s: %(message)s',
        level=logging.INFO,
    )

    service = get_service(args)

    if args.command == 'pull':
        pull(service, args.src_path, args.dst_path, args.r)

    elif args.command == 'push':
        push(service, args.src_path, args.dst_path, args.r)

    else:
        raise ValueError('unknown command ' + args.command)


if __name__ == '__main__':
    main()
