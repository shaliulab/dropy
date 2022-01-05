import os.path

from .utils import stopwatch

def save_raw_stream(dest, data):
    filehandle = open(dest, "wb", buffering=0)
    filehandle.write(data)
    filehandle.close()

def save_text_stream(dest, data):
    filehandle = open(dest, "w")
    filehandle.write(data)
    filehandle.close()

 
def find_folder(dbx, name):

    response = dbx.sharing_list_folders()
    entries = response.entries

    found = False
    for entry in entries:
        if entry.name == name:
            found = True
            break
    
    if found:
        return True, entry
    else:
        return False, None


# def download_shared_file(dbx, url, subfolder, name):

#     file_path = os.path.join(subfolder, name)
#     with stopwatch("get_shared_link_file"):
#         _, response = dbx.sharing_get_shared_link_file(
#             url = url,
#             path = file_path
#         )

#     data = response.content
#     return data