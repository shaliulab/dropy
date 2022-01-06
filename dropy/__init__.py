import json
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


    def init(self):

        access_token = get_access_token(**self.credentials)
        self._dropbox_handle = dropbox.Dropbox(oauth2_access_token=access_token)        
        self._current_account = self._dropbox_handle.users_get_current_account()


    def close(self):
        return self._dropbox_handle.close()

    @property
    def current_account(self):
        return self._current_account

    @property
    def root_namespace_id(self):
        return self.current_account.root_info.root_namespace_id

    # def init_dropbox(self):

    #     response = authenticate(**self.credentials)
    #     try:
    #         token = json.loads(response.text)["access_token"]
    #     except KeyError:
    #         logger.error("OAuth authentication failed")
    #         return 0
    #     dbx = dropbox.Dropbox(token)

    #     self._response = response
    #     self._dropbox_handle = dbx
