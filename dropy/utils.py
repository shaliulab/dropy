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

def get_metadata(dbx, file):
    try:
        logger.debug(f"files/get_metadata {file}")
        response = dbx.dbx.files_get_metadata(file, include_deleted=False)
    except Exception as error:
        response = error
    
    if type(response) is dropbox.exceptions.ApiError:
        # there was an error in the request
        if response.error._value.is_not_found():
            warnings.warn(f"{file} is not found in Dropbox server", stacklevel=2)
        elif response.error._value.is_malformed_path():
            warnings.warn(f"{file} is a malformed path", stacklevel=2)
        return False

    elif type(response) is dropbox.files.FileMetadata:
        return response
    
    else:
        raise Exception(f"files_get_metadata request on {file} had an unexpected return value {response}")


def file_exists(dbx, file):

    metadata=get_metadata(dbx, file)

    if type(metadata) is dropbox.files.FileMetadata:
        return metadata
    else:
        return False
