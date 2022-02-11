import unittest
import subprocess
import requests
import shutil
import os
import os.path

import dropy
from dropy.bin.dropy_init import BackgroundDropy
from dropy.web_utils import sync


class TestDownload(unittest.TestCase):

    def setUp(self):
        try:
            response = requests.post("http://localhost:9000", json = {})
        except Exception:
            raise Exception("Please make sure dropy is running in the background before testing it")

    
    def test_download_file(self):

        wd = os.getcwd()
        dest = os.path.join(wd, "tests/results/setup.py")
        assert not os.path.exists(dest)
        
        sync(
            "Dropbox:/Antonio/FSLLab/Projects/DropboxAPI/dropy/setup.py",
            dest
        )

        self.assertTrue(os.path.exists(dest))
        os.remove(dest)
    
    def test_download_folder(self):
        wd = os.getcwd()
        dest = os.path.join(wd, "tests/results/dropy/bin")
        assert not os.path.exists(dest)

        sync(
            "Dropbox:/Antonio/FSLLab/Projects/DropboxAPI/dropy/dropy/bin",
            dest
        )
        
        self.assertTrue(os.path.exists(dest))
        self.assertTrue(os.path.exists(os.path.join(dest, "dropy.py")))
        shutil.rmtree(dest)

    def test_cli(self):
        wd = os.getcwd()
        dest = os.path.join(wd, "tests/results/setup.py")
        assert not os.path.exists(dest)

        process = subprocess.Popen([
            "dropy",
            "Dropbox:/Antonio/FSLLab/Projects/DropboxAPI/dropy/setup.py",
            dest
        ])
        process.communicate()
        self.assertTrue(os.path.exists(dest))
        os.remove(dest)



if __name__ == "__main__":
    unittest.main()