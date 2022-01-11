import unittest
import argparse
import requests
import shutil
import datetime
import os
import os.path

import dropy
from dropy.bin.dropy_init import BackgroundDropy
from dropy.web_utils import sync, path_exists


class TestDownload(unittest.TestCase):

    def setUp(self):
        try:
            response = requests.post("http://localhost:9000", json = {})
        except Exception:
            raise Exception("Please make sure dropy is running in the background before testing it")

    
    def test_upload_file(self):

        date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        source = f"tests/static_data/test_upload/{date_time}_upload_test.txt"

        with open(source, "w") as filehandle:
            filehandle.write("Some data uploaded to Dropbox.\n")

        dest = "Dropbox:/Antonio/FSLLab/Projects/DropboxAPI/dropy/dropy/" + source

        wd = os.getcwd()
        sync(
            os.path.join(wd, source),
            dest
        )

        dest = dest.replace("Dropbox:", "")
        assert path_exists(dest)

    def test_upload_folder(self):
        wd = os.getcwd()

        date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        folder = f"tests/static_data/test_upload/{date_time}_folder/{date_time}_folder"
        os.makedirs(folder, exist_ok=True)

        for i in range(3):
            with open(os.path.join(folder, f"file_{i}"), "w") as filehandle:
                filehandle.write(f"{i}\n")
   
        sync(
            os.path.join(wd, folder),
            "Dropbox:/Antonio/FSLLab/Projects/DropboxAPI/dropy/dropy/" + folder,
        )
        
        assert path_exists("/Antonio/FSLLab/Projects/DropboxAPI/dropy/dropy/" + os.path.dirname(folder))
        shutil.rmtree(folder)


if __name__ == "__main__":
    unittest.main()