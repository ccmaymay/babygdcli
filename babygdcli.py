from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os


DIR_MIME_TYPE = 'application/vnd.google-apps.folder'
GOOGLE_APPS_MIME_TYPE_STEM = 'application/vnd.google-apps.'


def format_owner_names(owner_names):
    return ','.join(owner_names)

def format_mime_type(mime_type):
    return mime_type

def format_title(title, mime_type):
    if mime_type == DIR_MIME_TYPE:
        return title + '/'
    elif mime_type.startswith(GOOGLE_APPS_MIME_TYPE_STEM):
        return title + '@'
    else:
        return title


gauth = GoogleAuth(
    settings_file=os.path.expanduser('~/.babygdcli/settings.yaml')
)
gauth.LoadCredentialsFile()
gauth.CommandLineAuth()
gauth.SaveCredentialsFile()

drive = GoogleDrive(gauth)


def gen_paths(paths=None, root_abspath=None):
    if root_abspath is None:
        root_abspath = os.getcwd()

    if not paths:
        paths = ['.']

    for path in paths:
        abspath = os.path.abspath(path)
        if not abspath.startswith(root_abspath):
            raise Exception('%s is not under home' % abspath)

        relpath = abspath[len(root_abspath)+1:]

        yield (abspath, relpath)
