import json
import logging
import requests
import bottle
from dropy.core.data import Entry

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

def sync(source, dest, force_download=False, skip_existing_files=False):

    session = requests.Session()

    return session.post(
        "http://localhost:9000/sync",
        json={
            "source": source,
            "dest": dest,
            "yes": True,
            "force_download": force_download,
            "skip_existing_files": skip_existing_files
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