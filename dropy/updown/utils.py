import logging
import os.path
import datetime
import time
from pkg_resources import resource_filename

import contextlib
import yaml
import dropbox

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print('Total elapsed time for %s: %.3f' % (message, t1 - t0))


def should_be_ignored(name):
    if name.startswith('.'):
        print('Skipping dot file:', name)
        return True
    elif name.startswith('@') or name.endswith('~'):
        print('Skipping temporary file:', name)
        return True
    elif name.endswith('.pyc') or name.endswith('.pyo'):
        print('Skipping generated file:', name)
        return True
    else:
        return False


def already_synced(fullname, nname, name, listing):
    md = listing[nname]
    if os.path.exists(fullname):
        mtime = os.path.getmtime(fullname)
        mtime_dt = datetime.datetime(*time.gmtime(mtime)[:6])
        size = os.path.getsize(fullname)
        if (isinstance(md, dropbox.files.FileMetadata) and mtime_dt == md.client_modified and size == md.size):
            print(name, 'is already synced [stats match]')
            return True
        else:
            print(name, 'exists with different stats, downloading')
            return False
    else:
        print(name, 'does not exist, downloading')
        return False

def format_path(path):
    while '//' in path:
        path = path.replace('//', '/')
    
    return path


def get_shared_folders_urls():

    config_path = resource_filename("dropy", "data/config.yaml")

    logger.debug(f"Reading config from: {config_path}")

    with open(config_path, "r") as filehandle:
        config = yaml.load(filehandle, Loader=yaml.SafeLoader)
        
    urls = config["shared_folders"]

    logger.debug(f"Shared folders URL: {urls}")
    return urls

def save_raw_stream(dest, data):
    filehandle = open(dest, "wb", buffering=0)
    filehandle.write(data)
    filehandle.close()

def save_text_stream(dest, data):
    filehandle = open(dest, "w")
    filehandle.write(data)
    filehandle.close()


def check_downloaded_content_matches(res, fullname):

    with open(fullname, "rb") as f:
        data = f.read()

    name = os.path.basename(fullname)
    if res == data:
        print(name, 'is already synced [content match]')
        return True
    else:
        print(name, 'has changed since last sync')
        return False
