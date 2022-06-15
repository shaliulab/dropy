from dropy.utils import file_exists
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


    def file_exists(self, file):
        return file_exists(self._dbx, file)
