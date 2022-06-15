"""
Use as so

dropy-list -i foo/bar/NX/XXXX-XX-XX_XX-XX-XX

> outputs dropbox_status.txt, a plain text file where each filename is present, labeled either OK if found in the dropbox server and MISSING otherwise 
File labeled with NA if an error ocurred in the verification
"""

import os.path
import warnings
import logging
import asyncio
import aiofiles
import signal
import argparse

import tqdm
import yaml

from dropy.list import DropboxLister
from dropy.utils import load_config


logger = logging.getLogger(__name__)

try:
    from imgstore.constants import STORE_MD_FILENAME
except Exception as error:
    logger.debug(error)
    warnings.warn("imgstore could not be loaded. I will assume the experiments metadata are stored in metadata.yaml", stacklevel=2)
    STORE_MD_FILENAME="metadata.yaml"
    

config=load_config()

ROOT_PATH=config["root_path"]
OUTPUT_FILE="dropbox_status.txt"
STORE_ENTRY="__store"

def get_parser():

    ap=argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True, type=str, help="Path to flyhostel experiment")
    return ap

def read_metadata(input):
    with open(os.path.join(input, STORE_MD_FILENAME), "r") as filehandle:
        md=yaml.load(filehandle, yaml.SafeLoader)[STORE_ENTRY]

    assert "format" in md
    assert "interval" in md, f"Please specify {STORE_ENTRY}.interval"
    assert type(md["interval"]) is list and len(md["interval"]) == 2, "Plase specify _store.interval as a list of length 2"    
    return md

def get_extension(md):

    if md["format"] == "h264_nvenc/mp4":
        extension = "mp4"
    
    else:
        extension = "avi"

    return extension

def build_raw_data_list(chunk, video_extension):
    return [
        f"{str(chunk).zfill(6)}.{video_extension}",
        f"{str(chunk).zfill(6)}.png",
        f"{str(chunk).zfill(6)}.extra.json",
        f"{str(chunk).zfill(6)}.npz",
        f"{str(chunk).zfill(6)}.npy",
    ]


def build_idtrackerai_data_list(chunk):

    files = [
        "video_object.npy",
        "preprocessing/blobs_collection.npy",
        "preprocessing/fragments.npy",
        "preprocessing/global_fragments.npy",
        "trajectories/trajectories.npy",
        "accumulation_0/light_list_of_fragments.npy",
        "accumulation_0/model_params.npy",
        "accumulation_0/supervised_identification_network_.checkpoint.pth",
        "accumulation_0/supervised_identification_network_.model.pth",
    ]

    files = [f"idtrackerai/session_{str(chunk).zfill(6)}/{f}" for f in files]
    return files


def build_file_list(md, chunk):

    video_extension = get_extension(md)
    extra_cameras = md["extra_cameras"]
            
    files = []
    files += build_raw_data_list(chunk, video_extension)
    for camera in extra_cameras:
        folder = os.path.dirname(camera)
        extra_camera_files = files.copy()
        extra_camera_files.pop(extra_camera_files.index(f"{str(chunk).zfill(6)}.npy"))

        files+=[f"{folder}/{file}" for file in extra_camera_files]

    files+=build_idtrackerai_data_list(chunk)

    return files

async def check_file(lister, filehandle, file):

    async with aiofiles.open(OUTPUT_FILE, "a") as filehandle:
        try:
            found=await lister.file_exists(file)
            if found:
                message = f"{file}\tOK\n"
            else:
                message = f"{file}\tMISSING\n"
        except Exception as error:
            logger.error(error)
            message = f"{file}\tNA\n"

        await filehandle.write(message)
        await filehandle.flush()

async def _main():
    ap = get_parser()
    args = ap.parse_args()
    loop = asyncio.get_event_loop()

    if os.path.exists(OUTPUT_FILE):
        warnings.warn(f"{OUTPUT_FILE} exists, overwriting", stacklevel=2)
        with open(OUTPUT_FILE, "w") as filehandle:
            filehandle.write("")


    assert os.path.isdir(args.input)

    experiment = os.path.sep.join(args.input.split(os.path.sep)[::-1][:2][::-1])

    
    md = read_metadata(args.input)
    file_list = []
    for chunk in range(*md["interval"]):
        file_list += build_file_list(md, chunk)

    file_list=[f"{ROOT_PATH}/{experiment}/{file}" for file in file_list]

    coros=[]

    with DropboxLister() as lister:
        for file in file_list:
            coros.append(check_file(lister, filehandle, file))

    for i in range(0, len(coros), 10):
        try:
            await asyncio.gather(*(coros[i:min(i+10, len(coros))]))
        except KeyboardInterrupt:
            loop.close()
            return


def main():
    asyncio.run(_main())
