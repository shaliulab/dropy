import json
import os.path
import logging
import requests
import bottle
import dropbox
from dropy.core.data import Entry
from dropy.constants import DROPBOX_PREFIX, REMOTE_SEP 

logger = logging.getLogger(__name__)

try:
    from cheroot.wsgi import Server as WSGIServer # type: ignore
except ImportError:
    from cherrypy.wsgiserver import CherryPyWSGIServer as WSGIServer # type: ignore

class OurCherootServer(bottle.ServerAdapter):
    def run(self, handler): # pragma: no cover
        from cheroot import wsgi # type: ignore
        from cheroot.ssl import builtin # type: ignore
        self.options['bind_addr'] = (self.host, self.port)
        self.options['wsgi_app'] = handler
        certfile = self.options.pop('certfile', None)
        keyfile = self.options.pop('keyfile', None)
        chainfile = self.options.pop('chainfile', None)
        server = wsgi.Server(**self.options)
        if certfile and keyfile:
            server.ssl_adapter = builtin.BuiltinSSLAdapter(
                    certfile, keyfile, chainfile)
        try:
            server.start()
        finally:
            server.stop()


def set_server(host="0.0.0.0", port=9000):
    api = bottle.Bottle()
    server = "cheroot"

    try:
        #This checks if the patch has to be applied or not. We check if bottle has declared cherootserver
        #we assume that we are using cherrypy > 9
        from bottle import CherootServer
    except:
        #Trick bottle to think that cheroot is actulay cherrypy server, modifies the server_names allowed in bottle
        #so we use cheroot in background.
        server = "cherrypy"
        cheroot_server = OurCherootServer(host=host, port=port)
        bottle.server_names["cherrypy"] = cheroot_server
        logger.warning("Cherrypy version is bigger than 9, change to cheroot server")

    return api, bottle, server

def sync(source, dest, force_download=False, skip_existing_files=False, port=9000, ncores=1):
    f"""POST request a file between your local computer and the Dropbox server
    
    Arguments:
        source (str): Path to the original file in either Dropbox or your local pc. It **must** exist
        dest (str): Path to the destination file in either Dropbox or your local pc. It **may** exist
        skip_existing_files (bool):
            * If True and in download mode, existing files are skipped
            * If True and in upload mode, TODO

    
    Return:
        * When syncing a folder: None
        * When syncing a file: the file's Dropbox listing

       
    A path available in Dropbox must have the {DROPBOX_PREFIX}{REMOTE_SEP} prefix
    A running server spawned with `dropy-init --app-key <APP_KEY> --app-secret <APP_SECRET> should be running under port 9000
    """

    if f"{DROPBOX_PREFIX}{REMOTE_SEP}" in dest and skip_existing_files:
        raise NotImplementedError

    session = requests.Session()

    return session.post(
        f"http://localhost:{port}/sync",
        json={
            "source": source,
            "dest": dest,
            "yes": True,
            # "force_download": force_download,
            "skip_existing_files": skip_existing_files,
            "ncores": ncores
        }
    )

def list_folder(folder, recursive):

    session = requests.Session()

    url = "http://localhost:9000/list_folder"
    data = {
            "folder": folder,
            "recursive": recursive,
        }
    res = session.post(url, json=data)

    if res.ok:
        response = json.loads(res.content.decode())
        files = {}
        paths = {}
        for k, v in response["files"].items():
            files[k] = Entry(client_modified = v.client_modified, size = v.size)

        for k, v in response["paths"].items():
            paths[k] = Entry(client_modified = v.client_modified, size = v.size)

        response["files"] = files
        response["files"] = paths

        return response
    else:
        logger.warning(
            "Request could not be completed successfully"
            f" URL: {url}"
            f" JSON: {data}"
        )

def path_exists(path):
    
    session = requests.Session()

    url = "http://localhost:9000/path_exists"
    data = {
            "path": path,
        }
    res = session.post(url, json=data)

    if res.ok:
        response = json.loads(res.content.decode())
        return response[path]
    else:
        return False


def format_to_dropbox_api(dbx_handler, source, dest):
    """Given a source and a dest file or folder, format this information
    so it is compatible with the Dropbox API

    Arguments:
        dbx_handler (dropy.DropboxHandler): An OAUTH authenticated DropboxHandler instance
        source (str): Path to the original file in either Dropbox or your local pc. It **must** exist
        dest (str): Path to the destination file in either Dropbox or your local pc. It **may** exist
    
    """
    source = source.split(REMOTE_SEP)
    dest = dest.split(REMOTE_SEP)

    if len(source) == 2 and source[0] == DROPBOX_PREFIX and len(dest) == 1:
        remote_path = source[1]
        local_path = dest[0]
        direction = "down"

        # I only want it to work on download mode
        try:
            md = dbx_handler.dbx.files_get_metadata(
                path = remote_path
            )
        except dropbox.exceptions.ApiError:
            raise Exception (f"{remote_path} does not exist on Dropbox server")

    elif len(dest) == 2 and dest[0] == DROPBOX_PREFIX and len(source) == 1:
        remote_path = dest[1]
        local_path = source[0]
        direction = "up"
     # I only want it to work in upload mode
        assert os.path.exists(local_path), "Local file does not exist"

    assert remote_path.startswith(os.path.sep)
    remote_path = remote_path.split(os.path.sep)
    folder = "/".join(remote_path[:2])
    subfolder = os.path.dirname("/".join(remote_path[2:]))
    fullname = local_path
    
    logger.debug(
        "Syncing "
        f" Fullname {fullname}"
        f" Folder {folder}"
        f"  Subfolder {subfolder}"
    )

    return fullname, folder, subfolder, direction

