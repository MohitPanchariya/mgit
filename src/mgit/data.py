import os

MGIT_DIR = "./.mgit"

def init():
    '''
    This function is called when initialising a mgit repository.
    If the .mgit directory doesn't already exist, create one.
    If exists, raise a FileExists exception."
    '''
    if os.path.exists(MGIT_DIR):
        raise FileExistsError("Already a mgit repository.")
    else:
        os.makedirs(MGIT_DIR)
