import os.path

from .utils import stopwatch

def find_shared_folder(dbx, name):

    res = dbx.sharing_list_folders()
    entries = res.entries

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