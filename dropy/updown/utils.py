import os.path
import datetime
import time
from pkg_resources import resource_stream

import contextlib
import yaml
import dropbox

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
    mtime = os.path.getmtime(fullname)
    mtime_dt = datetime.datetime(*time.gmtime(mtime)[:6])
    size = os.path.getsize(fullname)
    if (isinstance(md, dropbox.files.FileMetadata) and mtime_dt == md.client_modified and size == md.size):
        return True
    else:
        return False

def format_path(path):
    while '//' in path:
        path = path.replace('//', '/')
    
    return path



def get_shared_folders_urls():
    
    config_path = resource_stream("dropy", "data/config.yaml")

    with open(config_path, "r") as filehandle:
        config = yaml.load(filehandle, Loader=yaml.SafeLoader)
        
    urls = config["shared_folders"]
    return urls 