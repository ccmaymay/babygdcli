#!/usr/bin/env python2.7


from babygdcli import drive, gen_paths
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


parser = ArgumentParser(
    formatter_class=ArgumentDefaultsHelpFormatter,
    description='pull/push individual files')
parser.add_argument('command', type=str, choices=('pull', 'push'),
                    help='command to execute against server')
parser.add_argument('path', type=str,
                    help='local/remote path to push/pull (respectively)')
parser.add_argument('-d', type=str)
args = parser.parse_args()

[(abspath, relpath)] = list(gen_paths([args.path], root_abspath=args.d))


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


if args.command == 'pull':
    entry_id = 'root'
    if relpath:
        relpath_pieces = relpath.split('/')
        for title in relpath_pieces:
            entry_id = get_entry_id(drive, entry_id, title)

    f = drive.CreateFile({'id': entry_id})
    f.GetContentFile(abspath)

elif args.command == 'push':
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

        f.SetContentFile(abspath)
        f.Upload()

else:
    raise ValueError('unknown command %s' % args.command)
