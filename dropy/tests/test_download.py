import unittest
import argparse
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
        sync(
            "Dropbox:/Antonio/FSLLab/Projects/DropboxAPI/dropy/setup.py",
            os.path.join(wd, "tests/results/setup.py")
        )

        assert os.path.exists("tests/results/setup.py")
        os.remove("tests/results/setup.py")
    
    def test_download_folder(self):
        wd = os.getcwd()
        sync(
            "Dropbox:/Antonio/FSLLab/Projects/DropboxAPI/dropy/dropy/bin",
            os.path.join(wd, "tests/results/dropy/bin")
        )
        
        assert os.path.exists("tests/results/dropy/bin")
        assert os.path.exists("tests/results/dropy/bin/dropy.py")
        shutil.rmtree("tests/results/dropy")

if __name__ == "__main__":
    unittest.main()