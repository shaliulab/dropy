import logging
import os.path
import joblib
import time
import dropbox
from dropy.oauth.official import get_access_token
from dropy.core.data import Entry
from dropy.updown import SyncMixin
logger = logging.getLogger(__name__)
LIMIT = 500


class DropboxHandler(SyncMixin):

    def __init__(self, app_key=None, app_secret=None):
        self._dropbox_handle = None
        self._current_account = None
        self._app_key = app_key
        self._app_secret = app_secret

    @property
    def credentials(self):
        return {
            "app_key": self._app_key,
            "app_secret": self._app_secret
        }

    @property
    def dbx(self):
        return self._dropbox_handle.with_path_root(dropbox.common.PathRoot.root(self.root_namespace_id))


    @property
    def current_account(self):
        return self._current_account

    @property
    def root_namespace_id(self):
        return self.current_account.root_info.root_namespace_id


    def init(self):

        access_token = get_access_token(**self.credentials)
        self._dropbox_handle = dropbox.Dropbox(oauth2_access_token=access_token)
        self._current_account = self._dropbox_handle.users_get_current_account()


    def close(self):
        return self._dropbox_handle.close()



    def get_metadata(self, path):
        return self.dbx.files_get_metadata(path)


    def list_entries(self, folder):
        listing = self.dbx.files_list_folder(folder, limit=LIMIT)
        entries = {entry.name: entry for entry in listing.entries}

        while listing.has_more:
            listing = self.dbx.files_list_folder_continue(listing.cursor)
            for entry in listing.entries:
                entries[entry.name] = entry
        
        return entries


    def split_into_files_paths_and_dirs(self, entries):

        dirs = {}
        files = {}
        paths = {}

        for entry in entries.values():
            if type(entry) is dropbox.files.FolderMetadata:
                dirs[entry.name] = None
            elif type(entry) is dropbox.files.FileMetadata:
                serializable_entry = Entry(
                    client_modified = entry.client_modified.strftime("%Y-%m-%d_%H-%M"),
                    size = entry.size
                )

                files[entry.name] = serializable_entry
                paths[entry.path_display] = serializable_entry

            else:
                logger.warning(f"{entry} is neither a folder nor a file")


        return files, paths, dirs


    def list_folder(self, folder, recursive=False, ncores=1):
        """

        Arguments:
           folder (str): Remote Dropbox folder
           recursive (bool, int):
               If True, the content of its subfolders is also queried, until the full directory tree is listed 
               If integer, only that amount of levels is recursively queried

        Returns:
            A length 2 list of lists,
            where the first element contains all the paths that point to a directory
            and the second element contains all the paths that point to a file
        """

        if recursive is True:
            recursive = True
        elif recursive == 0:
            recursive = False
        else:
            recursive -= 1

        print(f"Listing folder {folder}. recursive = {recursive}")

        assert folder.startswith("/")

        entries = self.list_entries(folder)
        files, paths, dirs = self.split_into_files_paths_and_dirs(entries)


        if recursive:

            if ncores == 1:
    
                output = []
    
                for directory in dirs:
                    output.append(self.list_folder(
                        os.path.join(
                            folder, directory
                        ), recursive=True, ncores=1
                    ))
            else:
            #for directory in dirs:
            #    output.append(self.list_folder(directory))
                output = joblib.Parallel(n_jobs=ncores)(
                    joblib.delayed(self.list_folder)(
                        os.path.join(
                            folder, directory
                        ),recursive=True, ncores=1
                    )
                    for directory in dirs
                )

            for entry in output:
                extra_files = entry["files"]
                extra_paths = entry["paths"]

                for entry_name, file in extra_files.items():
                    files[entry_name] = file
                for entry_path, path in extra_paths.items():
                    paths[entry_path] = path


        return {"dirs": dirs, "files": files, "paths": paths}
