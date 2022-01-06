"""Upload the contents of your Downloads folder to Dropbox.

This is an example app for API v2.
"""

from __future__ import print_function

import argparse
import logging
import os
import six
import sys
import unicodedata
import dropbox

from .utils import stopwatch, should_be_ignored, already_synced, get_shared_folders_urls, save_raw_stream, check_downloaded_content_matches
from .updown import upload, download
from .shared import find_shared_folder
from dropy.web_utils import list_folder as list_folder_request

if sys.version.startswith('2'):
    input = raw_input  # type: ignore # noqa: E501,F821; pylint: disable=redefined-builtin,undefined-variable,useless-suppression

logger = logging.getLogger(__name__)

# OAuth2 access token.  TODO: login etc.
def get_parser():
    parser = argparse.ArgumentParser(description='Sync rootdir to folder in Dropbox')
    parser.add_argument('folder', nargs='?', required=True,
                        help='Folder name in your Dropbox')
    parser.add_argument('rootdir', nargs='?', required=True,
                        help='Local directory to upload')
    parser.add_argument('--token', required=False,
                        help='Access token '
                        '(see https://www.dropbox.com/developers/apps)')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Answer yes to all questions')
    parser.add_argument('--no', '-n', action='store_true',
                        help='Answer no to all questions')
    parser.add_argument('--default', '-d', action='store_true',
                        help='Take default answer on all questions')

    return parser

def main(ap = None, args=None):
    """Main program.
    """

    if ap is None:
        parser = get_parser()
    else:
        parser = ap

    args = parser.parse_args()

    rootdir = args.rootdir
    folder = args.folder
    token = args.token
    yes = args.yes
    no = args.no
    default = args.default

    if sum([bool(b) for b in (yes, no, default)]) > 1:
        print('At most one of --yes, --no, --default is allowed')
        sys.exit(2)


    rootdir = os.path.expanduser(rootdir)

    return updown(rootdir, folder, yes, no, default, token=token)


def sync_file(dbx, fullname, folder, subfolder, args, shared=None, listing = None, force_download=None):
    """

    Push the contents of fullname to folder/subfolder/name in Dropbox
    or bring the content of folder/subfolder/name to fullname

    Args:
        dbx (dropbox.Dropbox): Authenticated dropbox handler
        fullname (str): Path in local computer to be synced to dropbox
        folder (str): Folder being synced to dropbox
        subfolder (str): Folder living inside folder that is currently being synced
        listing (dict): Files available in Dropbox website
        args (namespace): must contain no, yes, default
        **kwargs (dict): additional keyword arguments to upload and download

    Returns:
        None
    """


    name = os.path.basename(fullname)

    # NOTE
    # if shared is None, figure out whether the file belongs to a Dropbox shared folder
    # by checking whether folder is a key of shared_folders
    # if it is, replace folder with the URL
    # This is needed because the Dropbox API is different
    # if folder is shared (files_download / files_upload)
    # or not (sharing_get_shared_link_file / ?)
    folder_name = folder
    shared = False


    fullfolder = os.path.join(folder_name, subfolder)
    if not fullfolder.endswith("/"): fullfolder += "/"

    if not force_download and listing is None:
        listing = list_folder_request(fullfolder, recursive=False)["files"]
        listing = {file.replace(fullfolder, ""): listing[file] for file in listing}

    if not isinstance(name, six.text_type):
        name = name.decode('utf-8')
    nname = unicodedata.normalize('NFC', name)

    print(nname)
    if should_be_ignored(name):
        pass

    # it's available on dropbox.com -> download or upload
    elif force_download or nname in listing:
        if force_download:
            print(f"Forcing download of {fullname}")
            is_synced=False

        else:
            is_synced = already_synced(fullname, nname, name, listing)
        if is_synced:
            pass
        else:
            data = download(
                dbx, folder, subfolder, name,
                shared=shared
            )

            if os.path.exists(fullname):

                if not check_downloaded_content_matches(data, fullname):
                    if yesno('Refresh %s' % name, False, args):
                        upload(
                            dbx, fullname, folder, subfolder, name,
                            overwrite=True,
                            shared=shared
                        )
                    else:
                        save_raw_stream(
                            fullname, data
                        )
            else:
                save_raw_stream(
                    fullname, data
                )

    # it's NOT available on dropbox.com -> upload
    elif yesno('Upload %s' % name, True, args):
        if os.path.exists(fullname):
            upload(
                dbx, fullname, folder, subfolder, name,
                shared=shared
            )
        else:
            logger.warning(f"{fullname} does not exist")

    return listing

def updown(dbx, rootdir, folder, yes, no, default):
    """
    Parse command line, then iterate over files and directories under
    rootdir and upload all files.  Skips some temporary files and
    directories, and avoids duplicate uploads by comparing size and
    mtime with the server.
    """

    yesno_args = argparse.Namespace(yes=yes, no=no, default=default)

    print('Dropbox folder name:', folder)
    print('Local directory:', rootdir)
    if not os.path.exists(rootdir):
        print(rootdir, 'does not exist on your filesystem')
        sys.exit(1)
    elif not os.path.isdir(rootdir):
        print(rootdir, 'is not a folder on your filesystem')
        sys.exit(1)

    for dn, dirs, files in os.walk(rootdir):
        subfolder = dn[len(rootdir):].strip(os.path.sep)
        print('Descending into', subfolder, '...')

        # First do all the files.
        for name in files:
            fullname = os.path.join(dn, name)
            sync_file(dbx, fullname, folder, subfolder, yesno_args)


        # Then choose which subdirectories to traverse.
        keep = []
        for name in dirs:
            if name.startswith('.'):
                print('Skipping dot directory:', name)
            elif name.startswith('@') or name.endswith('~'):
                print('Skipping temporary directory:', name)
            elif name == '__pycache__':
                print('Skipping generated directory:', name)
            elif yesno('Descend into %s' % name, True, yesno_args):
                print('Keeping directory:', name)
                keep.append(name)
            else:
                print('OK, skipping directory:', name)
        dirs[:] = keep

    dbx.close()

def list_folder(dbx, folder, subfolder, shared=False):

    if shared:
        list_folder_shared_(dbx, folder, subfolder)

    else:
        return list_folder_(dbx, "/"+folder,  subfolder)

def list_folder_shared_(dbx, folder, subfolder):

    ret, res = find_shared_folder(dbx, folder)
    if ret:
        folder_id = res.shared_folder_id
        return list_folder_(dbx, f"id:{folder_id}", subfolder)
    else:
        raise Exception("Shared folder not found!")



def list_folder_(dbx, folder, subfolder):
    """List a folder.

    Return a dict mapping unicode filenames to
    FileMetadata|FolderMetadata entries.
    """
    path = '%s/%s' % (folder, subfolder.replace(os.path.sep, '/'))
    while '//' in path:
        path = path.replace('//', '/')
    path = path.rstrip('/')
    try:
        with stopwatch('list_folder'):
            res = dbx.files_list_folder(path)
    except dropbox.exceptions.ApiError as err:
        print('Folder listing failed for', path, '-- assumed empty:', err)
        return {}
    else:
        rv = {}
        for entry in res.entries:
            rv[entry.name] = entry


        logger.debug(rv)
        return rv


def yesno(message, default, args):
    """Handy helper function to ask a yes/no question.

    Command line arguments --yes or --no force the answer;
    --default to force the default answer.

    Otherwise a blank line returns the default, and answering
    y/yes or n/no returns True or False.

    Retry on unrecognized answer.

    Special answers:
    - q or quit exits the program
    - p or pdb invokes the debugger
    """
    if args.default:
        print(message + '? [auto]', 'Y' if default else 'N')
        return default
    if args.yes:
        print(message + '? [auto] YES')
        return True
    if args.no:
        print(message + '? [auto] NO')
        return False
    if default:
        message += '? [Y/n] '
    else:
        message += '? [N/y] '
    while True:
        answer = input(message).strip().lower()
        if not answer:
            return default
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        if answer in ('q', 'quit'):
            print('Exit')
            raise SystemExit(0)
        if answer in ('p', 'pdb'):
            import pdb
            pdb.set_trace()
        print('Please answer YES or NO.')



class SyncMixin:
    """
    Requires self._dropbox_handler to be set to a dropbox.Dropbox instance
    """

    def sync_folder(self, local_folder, dropbox_folder):

        folder = dropbox_folder
        rootdir = local_folder
        return updown(self.dbx, rootdir, folder, yes=None, no=None, default=None)


    def sync_file(self, fullname, folder, subfolder, yes=None, no=None, default=None, listing=None, force_download=None):

        yesno_args = argparse.Namespace(yes=yes, no=no, default=default)

        return sync_file(
            dbx=self.dbx,
            fullname=fullname,
            folder=folder,
            subfolder=subfolder,
            args=yesno_args,
            listing=listing,
            force_download=force_download
        )




if __name__ == '__main__':
    main()
