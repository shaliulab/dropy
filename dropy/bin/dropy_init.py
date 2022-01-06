import os
import os.path
import json
import logging
import dropbox
from dropy import DropboxDownloader
from dropy.oauth.official import get_parser
from dropy.web_utils import set_server
import dropbox

logger = logging.getLogger(__name__)
logging.getLogger("dropy.updown.utils").setLevel(logging.DEBUG)
logging.getLogger("dropy.updown.base").setLevel(logging.DEBUG)

DEBUG = True
PORT = 9000
api, bottle, server = set_server(host="0.0.0.0", port=PORT)

def main(ap=None, args=None):

    if args is None:
        ap = get_parser(ap)
        args = ap.parse_args()

    global dbx
    dbx = DropboxDownloader(
        app_key=args.app_key,
        app_secret=args.app_secret
    )

    dbx.init()
    bottle.run(api, host='0.0.0.0', port=PORT, debug=DEBUG, server=server)


@api.post("/sync")
def sync():
    data = bottle.request.body.read()
    data = json.loads(data)
    print(data)

    source = data.pop("source").split(":")
    dest = data.pop("dest").split(":")


    if len(source) == 2 and source[0] == "Dropbox" and len(dest) == 1:
        remote_path = source[1]
        local_path = dest[0]

        # I only want it to work on download mode
        try:
            md = dbx.dbx.files_get_metadata(
                path = remote_path
            )
        except dropbox.exceptions.ApiError:
            raise Exception ("Remote file does not exist")

    elif len(dest) == 2 and dest[0] == "Dropbox" and len(source) == 1:
        remote_path = dest[1]
        local_path = source[0]
        # I only want it to work in upload mode
        assert os.path.exists(local_path), "Local file does not exist"
    
    assert remote_path.startswith(os.path.sep)
    remote_path = remote_path.split(os.path.sep)
    folder = "/".join(remote_path[:2])
    subfolder = os.path.dirname("/".join(remote_path[2:]))
    fullname = local_path

    print(data)


    # to download
    dbx.sync_file(
        fullname,
        folder,
        subfolder,
        **data
    )

@api.get("/list_folder/<folder>")
def list_folder(folder):
    return dbx.list_folder(folder)


@api.get("/info")
def info():
    return dbx.current_account.__str__()


@api.get("/close")
def close(exit_status=0):
    logger.info("Closing...")
    dbx.close()
    os._exit(exit_status)



if __name__ == "__main__":
    main()
