import logging
import sys
import codecs
import httplib2
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'
GOOGLE_APPS_MIME_TYPE_STEM = 'application/vnd.google-apps.'

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'

CREDENTIALS_PATH = os.path.expanduser('~/.babygdcli/gauth.cred')
CLIENT_SECRETS_PATH = os.path.expanduser('~/.babygdcli/client_secrets.json')
APPLICATION_NAME = 'babygdcli'


def mkdirp(path):
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        except IOError as e:
            if not os.path.isdir(path):
                raise e


def mkdirp_parent(path):
    parent_path = os.path.dirname(path)
    if parent_path:
        mkdirp(parent_path)


def format_owner_names(owner_names):
    return ','.join(owner_names)


def format_mime_type(mime_type):
    return mime_type


def format_title(title, mime_type):
    if mime_type == FOLDER_MIME_TYPE:
        return title + '/'
    elif mime_type.startswith(GOOGLE_APPS_MIME_TYPE_STEM):
        return title + '@'
    else:
        return title


def get_credentials(args):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    mkdirp_parent(CREDENTIALS_PATH)
    store = Storage(CREDENTIALS_PATH)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRETS_PATH, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, args)
        logging.info('storing credentials to ' + CREDENTIALS_PATH)
    return credentials


def get_service(args):
    credentials = get_credentials(args)
    http = credentials.authorize(httplib2.Http())
    return discovery.build('drive', 'v3', http=http)


def search(service, parent_file_id, name):
    response = service.files().list(
        q="'{}' in parents and name='{}' and trashed=false".format(
             parent_file_id, name.replace("'", r"\'")),
    ).execute()
    for f in response.get('files', []):
        yield f


class NoSuchFile(Exception):
    def __init__(self, path):
        Exception.__init__(self, '%s does not exist' % path)


def get_file_id(drive, parent_file_id, name):
    files = list(search(drive, parent_file_id, name))
    if len(files) < 1:
        raise NoSuchFile(name)
    elif len(files) > 1:
        logging.warning(
            '{} in {} more than one match'.format(name, parent_file_id))
    return files[0].get('id')


def set_stdout_encoding():
    if sys.version_info[0] < 3:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    else:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())


def get_arg_parser(description):
    return ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        parents=[tools.argparser],
        description=description,
    )
