"""Upload the contents of your Downloads folder to Dropbox.

This is an example app for API v2.
"""

from __future__ import print_function

import argparse
import logging
import os
import traceback

import six
import sys
import unicodedata
import dropbox
import joblib

from .utils import stopwatch, should_be_ignored, already_synced, get_shared_folders_urls, save_raw_stream, check_downloaded_content_matches, sanitize_path
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

def sync_folder_(
    dbx_handler, fullname, folder, subfolder, args, direction, listing = None,
    skip_existing_files=False, force_download=False, ncores=1, recursive=True,
):

    """Make sure the content of a remote folder and a local folder match

    Arguments:
        dbx_handler (dropy.DropboxHandler): An OAUTH authenticated DropboxHandler instance
        fullname (str): Path in local computer to be synced to Dropbox. It may or not exist
        folder (str): Root folder being synced to Dropbox ("/foo")
        subfolder (str): Folder where the folder to be synced lives, relative to the root folder ("bar")
        args: (argparse.Namespace): namespace with defined yes no and default values.
            Used to establish whether the user is prompted and with what default answer
        direction (str): Either up or down
        skip_existing_files (bool):
            * If True and in download mode, existing files are skipped
            * If True and in upload mode, TODO

        ncores (int): number of CPUs to use in listing and syncing of files

    Return: None

    All contents of fullname will reflect those in the dropbox folder folder/subfolder/folder_name
    where folder_name is the os.path.basename(fullname)    
    """

    if direction == "up" and skip_existing_files:
        raise NotImplementedError

    # TODO Remove all force_download and then remove **kwargs, which is there
    # just to accept this unused variable

    if direction == "down":
        folder_name = os.path.basename(fullname.rstrip("/"))
        rootdir = os.path.dirname(fullname.rstrip("/"))
        mirrored_folder = fullname

        dropbox_rootdir = os.path.join(folder, subfolder)
        dropbox_folder = os.path.join(dropbox_rootdir, folder_name)
        data = dbx_handler.list_folder(
            dropbox_folder, recursive=recursive, ncores=ncores
        )

        paths = [p.replace(dropbox_rootdir, rootdir) for p in data["paths"].keys()]
 
    elif direction == "up":
        # TODO Not tested
        raise NotImplementedError

        fullfolder = fullname
        dirlist = [fullname]
        paths = []

        dropbox_folder = folder

        while len(dirlist) > 0:
            for (dirpath, dirnames, filenames) in os.walk(dirlist.pop()):
                dirlist.extend(dirnames)
                paths.extend(map(lambda n: os.path.join(*n), zip([dirpath] * len(filenames), filenames)))

        fullnames = []
        for path in paths:
            filename = path.replace(fullfolder, "").lstrip("/")
            fullnames.append(os.path.join(fullname, filename))
        
        paths = fullnames

    return sync_files(
        dbx_handler.dbx,
        paths,
        dropbox_folder,
        mirrored_folder,
        args,
        ncores=ncores,
        skip_existing_files=skip_existing_files,
    )

def sync_files(dbx, paths, folder, rootdir, args, ncores=1, **kwargs):


    subfolders = []
    for i, path in enumerate(paths):
        subfolders.append(os.path.dirname(paths[i]).replace(rootdir, "").lstrip("/"))


    if ncores == 1:
        for i, path in enumerate(paths):
            sync_file_(
                dbx,
                fullname = paths[i],
                folder = folder,
                subfolder = subfolders[i],
                args=args,
                **kwargs
            )

    else:

        joblib.Parallel(n_jobs=ncores)(
            joblib.delayed(sync_file_)(
                dbx,
                paths[i],
                folder,
                subfolders[i],
                args=args,
                **kwargs
            )
            for i, _ in enumerate(paths)
        )

    return None
        
    
    # for path in paths:
    #     filename = path.replace(fullfolder, "").lstrip("/")
    #     fullname_one_iter = os.path.join(fullname, filename)
        
    #     sync_file_(
    #         dbx_handler.dbx,
    #         fullname = fullname_one_iter,
    #         folder = dropbox_folder,
    #         subfolder = dropbox_subfolder,
    #         skip_existing_files=skip_existing_files,
    #         args=args
    #     )

    return None

def sync_file_(
    dbx, fullname, folder, subfolder, args,
    shared=None, listing = None, force_download=False,
    skip_existing_files=False, skip_listing=False
    ):

    """Push the contents of fullname to folder/subfolder/name in Dropbox
    or bring the content of folder/subfolder/name to fullname

    Arguments:
        dbx (dropbox.Dropbox): Authenticated dropbox handler
        fullname (str): Path in local computer to be synced to Dropbox. It may or not exist
        folder (str): Folder being synced to dropbox
        subfolder (str): Folder living inside folder that is currently being synced
        listing (dict): Files available in Dropbox website
        args (argparse.Namespace): must contain no, yes, default
        **kwargs (dict): additional keyword arguments to upload and download

    Return:
        None
    """


    name = os.path.basename(fullname)
    if not isinstance(name, six.text_type):
        name = name.decode('utf-8')
    nname = unicodedata.normalize('NFC', name)

    if should_be_ignored(name):
        return None

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

    if not skip_listing and listing is None:
        try:
            path = sanitize_path(os.path.join(folder, subfolder, name))
            md = dbx.files_get_metadata(path)
            
            listing = {os.path.basename(md.path_display): md}
            listing = {file.replace(fullfolder, ""): listing[file] for file in listing}
        except Exception as error:
            logger.warning(error)
            logger.warning(traceback.print_exc())
            raise Exception(f"Could not query {path} to get a listing for {fullname}")


    # it's available on dropbox.com -> download or upload
    if listing is None or nname in listing:
        if skip_existing_files and os.path.exists(fullname):
            is_synced=True
        else:
            is_synced = already_synced(fullname, nname, name, listing)
        
        if is_synced:
            return listing

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
            sync_file_(dbx, fullname, folder, subfolder, yesno_args)


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
        return list_folder_shared_(dbx, folder, subfolder)

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


    def sync_folder(self, fullname, folder, subfolder, args, **kwargs):
        
        return sync_folder_(
            dbx_handler=self,
            fullname=fullname,
            folder=folder,
            subfolder=subfolder,
            args=args,
            **kwargs
        )



    def sync_file(self, fullname, folder, subfolder, args, **kwargs):

        return sync_file_(
            dbx=self.dbx,
            fullname=fullname,
            folder=folder,
            subfolder=subfolder,
            args=args,
            **kwargs
            )

    def sync(
        self, fullname, folder, subfolder,  yes=None, no=None, default=None,
        force_download=False, listing=None, **kwargs
    ):

        yesno_args = argparse.Namespace(yes=yes, no=no, default=default)

        FUNCS = {"file": self.sync_file, "folder": self.sync_folder}

        if os.path.exists(fullname):
            if os.path.isdir(fullname):
                isdir = True
                isfile = False
            elif os.path.isfile(fullname):
                isdir = False
                isfile = True
        
        else:
            md = self.dbx.files_get_metadata(
                os.path.join(folder, subfolder, os.path.basename(fullname))
            )

            if isinstance(md, dropbox.files.FileMetadata):
                isfile = True
                isdir = False

            elif isinstance(md, dropbox.files.FolderMetadata):
                isfile = False
                isdir = True

        
        if isfile and not isdir:
            key = "file"

        elif isdir and not isfile:
            key = "folder"
        
        else:
            raise Exception("Path is either file and dir or neither file and dir")

        
        if key == "file":
            kwargs.pop("direction", None)
            kwargs.pop("recursive", None)

        FUNCS[key](
            fullname=fullname,
            folder=folder,
            subfolder=subfolder,
            args=yesno_args,
            listing=listing,
            force_download=force_download,
            **kwargs
        )

if __name__ == '__main__':
    main()
