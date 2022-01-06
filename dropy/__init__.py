import logging
import dropbox
from dropy.oauth.official import get_access_token
from .updown import SyncMixin
logger = logging.getLogger(__name__)


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


    def list_folder(self, folder):
        """

        Arguments:
           folder: Remote Dropbox folder
        
        Returns:
            A length 2 tuple of lists,
            where the first element contains all the paths that map to a directory
            and the second element contains all the paths that map to a file  
        """
        assert folder.startswith("/")
        folder_result = self.dbx.files_list_folder(folder)
        entries = folder_result.entries
        
        dirs = []
        files = []
        for entry in entries:
            if type(entry) is dropbox.files.FolderMetadata:
                dirs.append(entry.path_display)
            elif type(entry) is dropbox.files.FileMetadata:
                files.append(entry.path_display)
            else:
                logger.warning(f"{entry} is neither a folder nor a file")
        
        return dirs, files
