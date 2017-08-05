#!/usr/bin/env python2.7


import logging
import os

from apiclient.http import MediaFileUpload, MediaIoBaseDownload

from babygdcli import (
    get_service, get_file, NoSuchFile, get_arg_parser, FOLDER_MIME_TYPE,
    mkdirp
)


def pull_file(service, file_id, src_path, dst_path):
    request = service.files().get_media(fileId=file_id)
    with open(dst_path, 'w') as f:
        downloader = MediaIoBaseDownload(f, request)
        (status, done) = downloader.next_chunk()
        while done is False:
            logging.info('downloading... {:.2f}%'.format(
                status.progress() * 100))
            (status, done) = downloader.next_chunk()

    logging.info('{} <- {}'.format(dst_path, src_path))


def pull(service, src_path, dst_path):
    if os.path.isdir(dst_path):
        dst_path = os.path.join(dst_path, src_path.split('/')[-1])

    file_id = 'root'
    src_components = src_path.split('/')
    for name in src_components:
        f = get_file(service, file_id, name)
        file_id = f['id']

    if f['mimeType'] == FOLDER_MIME_TYPE:
        queue = [(src_path, dst_path, file_id)]

        while queue:
            (src_parent_path, dst_parent_path, parent_file_id) = queue.pop()
            mkdirp(dst_parent_path)
            response = service.files().list(
                q="'{}' in parents and trashed=false".format(parent_file_id),
            ).execute()
            for f in response.get('files', []):
                src_path = '/'.join((src_parent_path, f['name']))
                dst_path = os.path.join(dst_parent_path, f['name'])
                if f['mimeType'] == FOLDER_MIME_TYPE:
                    queue.insert(0, (src_path, dst_path, f['id']))
                else:
                    pull_file(service, f['id'], src_path, dst_path)

    else:
        pull_file(service, f['id'], src_path, dst_path)


def push_file(service, file_id, name, src_path, dst_path):
    if os.stat(src_path).st_size == 0:
        try:
            f = get_file(service, file_id, name)
        except NoSuchFile:
            pass
        else:
            service.files().delete(fileId=f['id']).execute()

        service.files().create(
            body=dict(
                name=name,
                parents=[file_id],
            ),
            media_body=None,
        ).execute()

    else:
        media_body = MediaFileUpload(src_path, resumable=True)
        try:
            f = get_file(service, file_id, name)
        except NoSuchFile:
            request = service.files().create(
                body=dict(
                    name=name,
                    parents=[file_id],
                ),
                media_body=media_body,
            )
        else:
            request = service.files().update(
                fileId=f['id'],
                media_body=media_body,
            )

        (status, response) = request.next_chunk()
        while response is None:
            logging.info('uploading... {:.2f}%'.format(
                status.progress() * 100))
            (status, response) = request.next_chunk()

    logging.info('{} -> {}'.format(src_path, dst_path))


def drive_mkdirp_shallow(service, file_id, name):
    try:
        return get_file(service, file_id, name)['id']
    except NoSuchFile:
        response = service.files().create(
            body=dict(
                name=name,
                parents=[file_id],
                mimeType=FOLDER_MIME_TYPE,
            ),
            fields='id',
        ).execute()
        return response.get('id')


def push(service, src_path, dst_path):
    file_id = 'root'

    if dst_path == '.' or dst_path == '/' or dst_path == './':
        name = os.path.basename(src_path)
        dst_path = name

    else:
        dst_components = dst_path.split('/')

        for name in dst_components[:-1]:
            file_id = drive_mkdirp_shallow(service, file_id, name)

        name = dst_components[-1]
        try:
            f = get_file(service, file_id, name)
            if f['mimeType'] == FOLDER_MIME_TYPE:
                dst_path = '/'.join((dst_path, os.path.basename(src_path)))
                file_id = f['id']
                name = os.path.basename(src_path)
        except NoSuchFile:
            pass

    if os.path.isdir(src_path):
        file_id = drive_mkdirp_shallow(service, file_id, name)
        queue = [(src_path, dst_path, file_id)]

        while queue:
            (src_parent_path, dst_parent_path, parent_file_id) = queue.pop()
            for name in os.listdir(src_parent_path):
                src_path = os.path.join(src_parent_path, name)
                dst_path = '/'.join((dst_parent_path, name))
                if os.path.isdir(src_path):
                    file_id = drive_mkdirp_shallow(service, parent_file_id,
                                                   name)
                    queue.insert(0, (src_path, dst_path, file_id))
                else:
                    push_file(service, parent_file_id, name, src_path,
                              dst_path)

    else:
        push_file(service, file_id, name, src_path, dst_path)


def main():
    parser = get_arg_parser('pull/push individual files')
    parser.add_argument('command', type=str, choices=('pull', 'push'),
                        help='command to execute against server')
    parser.add_argument('src_path', type=str,
                        help='local/remote path to push/pull, respectively')
    parser.add_argument('dst_path', type=str,
                        help='remote/local path to push/pull to, respectively')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)-15s %(levelname)s: %(message)s',
        level=logging.INFO,
    )

    service = get_service(args)

    if args.command == 'pull':
        pull(service, args.src_path, args.dst_path)

    elif args.command == 'push':
        push(service, args.src_path, args.dst_path)

    else:
        raise ValueError('unknown command ' + args.command)


if __name__ == '__main__':
    main()
