from core import (
    drive, DIR_MIME_TYPE, GOOGLE_APPS_MIME_TYPE_STEM,
    format_owner_names, format_mime_type, format_title,
    gen_paths
)
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('paths', metavar='path', nargs='*', type=str)
parser.add_argument('-l', action='store_true')
parser.add_argument('-t', action='store_true')
ns = parser.parse_args()


for (abspath, relpath) in gen_paths(ns.paths):
    parent_id = 'root'
    if relpath:
        relpath_pieces = relpath.split('/')
        for title in relpath_pieces:
            parents = drive.ListFile({'q': "'%s' in parents and title='%s' and trashed=false" % (parent_id, title)}).GetList()
            if len(parents) < 1:
                raise Exception('%s does not exist' % title)
            elif len(parents) > 1:
                raise Exception('%s has more than one parent?' % title)
            parent_id = parents[0]['id']
            if "'" in parent_id:
                raise Exception('%s has evil id %s' % (parents[0]['title'], parent_id))

    query = "'%s' in parents and trashed=false" % parent_id
    files = drive.ListFile({'q': query}).GetList()


    if files:
        max_owner_names_len = max(len(format_owner_names(f['ownerNames'])) for f in files)
        owner_names_template = '%%%ds' % max_owner_names_len


        max_mime_type_len = max(len(format_mime_type(f['mimeType'])) for f in files)
        mime_type_template = '%%%ds' % max_mime_type_len


        if ns.t:
            files.sort(key=lambda f: f['modifiedDate'], reverse=True)

        for f in files:
            if ns.l:
                print '%s%s %s %s %s %s' % (
                    'w' if f['editable'] else '-',
                    's' if f['shared'] else '-',
                    owner_names_template % format_owner_names(f['ownerNames']),
                    mime_type_template % format_mime_type(f['mimeType']),
                    f['modifiedDate'],
                    format_title(f['title'], f['mimeType']),
                )
            else:
                print format_title(f['title'], f['mimeType'])