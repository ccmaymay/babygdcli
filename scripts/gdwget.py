#!/usr/bin/env python2.7


import logging
import os
import re

from apiclient.http import MediaIoBaseDownload

from babygdcli import (
    get_service, get_arg_parser, FOLDER_MIME_TYPE, mkdirp
)


URL_RE = re.compile(r'/d/([^/]w+)/')


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


def pull_url(service, src_url, dst_path):
    if os.path.isdir(dst_path):
        raise Exception('destination path already exists: {}'.format(dst_path))

    file_id = URL_RE.search(src_url).group(1)
    f = service.files().get(fileId=file_id)

    if f['mimeType'] == FOLDER_MIME_TYPE:
        queue = [(None, dst_path, file_id)]

        while queue:
            (src_parent_path, dst_parent_path, parent_file_id) = queue.pop()
            mkdirp(dst_parent_path)
            response = service.files().list(
                q="'{}' in parents and trashed=false".format(parent_file_id),
            ).execute()
            for f in response.get('files', []):
                if src_parent_path is None:
                    src_path = src_parent_path
                else:
                    src_path = '/'.join((src_parent_path, f['name']))
                dst_path = os.path.join(dst_parent_path, f['name'])
                if f['mimeType'] == FOLDER_MIME_TYPE:
                    queue.insert(0, (src_path, dst_path, f['id']))
                else:
                    pull_file(service, f['id'], src_path, dst_path)

    else:
        pull_file(service, f['id'], src_path, dst_path)


def main():
    parser = get_arg_parser('pull/push individual files')
    parser.add_argument('src_url', type=str,
                        help='Google drive URL to pull from')
    parser.add_argument('dst_path', type=str,
                        help='local path to pull to')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)-15s %(levelname)s: %(message)s',
        level=logging.INFO,
    )

    service = get_service(args)

    pull_url(service, args.src_url, args.dst_path)


if __name__ == '__main__':
    main()
