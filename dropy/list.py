from dropy.utils import get_metadata, file_exists
from dropy import DropboxHandler

class DropboxLister:

    def __init__(self):
        self._dbx = DropboxHandler()
        self._dbx.init()

    
    def close(self):
        self._dbx.close()
   
    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

    async def file_exists(self,  *args, **kwargs):
        return file_exists(self._dbx, *args, **kwargs)


    async def get_metadata(self, *args, **kwargs):
        return get_metadata(self._dbx, *args, **kwargs)
