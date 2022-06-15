import warnings
import logging
import json
import dropbox
from dropy.constants import CONFIG_FILE

logger = logging.getLogger(__name__)

def load_config():
    with open(CONFIG_FILE, "r") as filehandle:
        config = json.load(filehandle)
    
    return config

def save_config(config):
    with open(CONFIG_FILE, "w") as filehandle:
            json.dump(config, filehandle)

def file_exists(dbx, file):
    try:
        logger.debug(f"files/get_metadata {file}")
        returns = dbx.dbx.files_get_metadata(file, include_deleted=False)
    except Exception as error:
        returns = error
    
    if type(returns) is dropbox.exceptions.ApiError:
        # there was an error in the request

        if returns.error._value.is_not_found():
            warnings.warn(f"{file} is not found in Dropbox server", stacklevel=2)
        elif returns.error._value.is_malformed_path():
            warnings.warn(f"{file} is a malformed path", stacklevel=2)
        return False

    elif type(returns) is dropbox.files.FileMetadata:
        return True
    
    else:
        raise Exception(f"files_get_metadata request on {file} had an unexpected return value {returns}")