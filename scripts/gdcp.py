#!/usr/bin/env python2.7


from babygdcli import drive, gen_paths
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging
import os


parser = ArgumentParser(
    formatter_class=ArgumentDefaultsHelpFormatter,
    description='pull/push individual files')
parser.add_argument('command', type=str, choices=('pull', 'push'),
                    help='command to execute against server')
parser.add_argument('paths', type=str, nargs='+', metavar='path',
                    help='local/remote paths to push/pull (respectively)')
parser.add_argument('-r', action='store_true')
args = parser.parse_args()


def get_entries(drive, entry_id, title):
    return drive.ListFile({
        'q': "'%s' in parents and title='%s' and trashed=false" %
             (entry_id, title)
    }).GetList()


def check_entry_id(entry_id, title):
    if "'" in entry_id:
        raise Exception('%s has evil id %s' % (title, entry_id))


class NoSuchFolder(Exception):
    def __init__(self, path):
        Exception.__init__(self, '%s does not exist' % path)


def get_entry_id(drive, entry_id, title):
    entries = get_entries(drive, entry_id, title)
    if len(entries) < 1:
        raise NoSuchFolder(title)
    elif len(entries) > 1:
        raise Exception('%s has more than one parent?' % title)
    entry_id = entries[0]['id']
    check_entry_id(entry_id, entries[0]['title'])
    return entry_id


def mixed_paths_to_file_paths(paths):
    for path in paths:
        if os.path.isfile(path):
            yield path
        else:
            for (parent_path, dir_entries, file_entries) in os.walk(path):
                for file_entry in file_entries:
                    yield os.path.join(parent_path, file_entry)


logger = logging.getLogger('babygdcli')
stderr_handler = logging.StreamHandler()
stderr_handler.setFormatter(logging.Formatter(
    fmt='%(asctime)-15s %(levelname)s: %(message)s'
))
logger.addHandler(stderr_handler)
logger.setLevel(logging.INFO)


if args.command == 'pull':
    for (abspath, relpath) in gen_paths(args.paths):
        local_path = abspath
        remote_path = relpath

        if args.r:
            raise Exception('recursive pull not yet implemented')

        entry_id = 'root'
        if relpath:
            relpath_pieces = relpath.split('/')
            for title in relpath_pieces:
                entry_id = get_entry_id(drive, entry_id, title)

        f = drive.CreateFile({'id': entry_id})
        f.GetContentFile(abspath)

        logger.info(
            '%s <- %s' %
            (local_path, remote_path)
        )

elif args.command == 'push':
    if args.r:
        paths = mixed_paths_to_file_paths(args.paths)
        raise Exception('recursive pull not yet implemented')
    else:
        paths = args.paths

    for (abspath, relpath) in gen_paths(paths):
        local_path = abspath
        remote_path = relpath

        entry_id = 'root'
        title = ''

        if relpath:
            relpath_pieces = relpath.split('/')
            for title in relpath_pieces[:-1]:
                try:
                    new_entry_id = get_entry_id(drive, entry_id, title)
                except NoSuchFolder:
                    d = drive.CreateFile()
                    d['title'] = title
                    d['parents'] = [{'id': entry_id}]
                    d['mimeType'] = 'application/vnd.google-apps.folder'
                    d.Upload()
                    entries = [d]
                    entry_id = d['id']
                    check_entry_id(entry_id, d['title'])
                else:
                    entry_id = new_entry_id

            title = relpath_pieces[-1]
            try:
                new_entry_id = get_entry_id(drive, entry_id, title)
            except NoSuchFolder:
                f = drive.CreateFile({
                    'title': title,
                    'parents': [{'id': entry_id}]
                })
                f.Upload()
                entries = [f]
                check_entry_id(f['id'], f['title'])
            else:
                entry_id = new_entry_id
                f = drive.CreateFile({'id': entry_id})

            f.SetContentFile(abspath)
            f.Upload()

        logger.info(
            '%s -> %s' %
            (local_path, remote_path)
        )

    else:
        raise ValueError('unknown command %s' % args.command)
