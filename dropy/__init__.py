import logging
import os.path
import joblib
import time
import dropbox
from dropy.oauth.official import get_access_token
from dropy.core.data import Entry
from .updown import SyncMixin
logger = logging.getLogger(__name__)

LIMIT = 500


class DropboxDownloader(SyncMixin):

    def __init__(self, app_key, app_secret):
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

    def list_folder(self, folder, recursive=False):
        """

        Arguments:
           folder: Remote Dropbox folder

        Returns:
            A length 2 list of lists,
            where the first element contains all the paths that map to a directory
            and the second element contains all the paths that map to a file
        """
        if recursive is True:
            recursive = True
        elif recursive == 0:
            recursive = False
        else:
            recursive -= 1
        print(f"Listing folder {folder} with recursive {recursive}")


        assert folder.startswith("/")
        folder_result = self.dbx.files_list_folder(folder, limit=LIMIT)
        entries = {entry.name: entry for entry in folder_result.entries}
        while folder_result.has_more:
            logger.info(f"{len(folder_result.entries)} entries downloaded")
            print(f"{len(folder_result.entries)} entries downloaded")
            logger.debug("calling list_folder_continue. length of entries = {len(entries)}")
            print(f"calling list_folder_continue. length of entries = {len(entries)}")
            folder_result = self.dbx.files_list_folder_continue(folder_result.cursor)
            for entry in folder_result.entries:
                entries[entry.name] = entry

        print(f"All {len(entries)} have been fetched")

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

        if recursive:

            output = []
            #for directory in dirs:
            #    output.append(self.list_folder(directory))
            output = joblib.Parallel(n_jobs=-2)(
                joblib.delayed(
                    self.list_folder
                )(os.path.join(folder, directory), recursive=recursive)
                for directory in dirs
            )

            for entry in output:
                extra_files = entry["files"]
                extra_paths = entry["paths"]

                for entry_name, file in extra_files.items():
                    files[entry_name] = file
                for entry_path, file in extra_paths.items():
                    paths[entry_path] = file


        return {"dirs": [], "files": files, "paths": paths}
