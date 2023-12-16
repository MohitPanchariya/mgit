import os
import hashlib

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
        os.makedirs(os.path.join(MGIT_DIR, "objects"))


def hashObject(filePath):
    '''
    This function is used to create a blob object and store in the
    object database of the mgit repository. 
    '''
    if not os.path.exists(MGIT_DIR):
        raise FileNotFoundError("This is not a mgit repository."\
                                "Use the mgit init command to make this a git repository.")
    else:
        with open(filePath, "rb") as file:
            data = file.read()
        
        # oid => object id
        oid = hashlib.sha1(data).hexdigest()

        # Create a blob object in the object database
        with open(os.path.join(os.getcwd(), MGIT_DIR, "objects", oid), "wb") as file:
            file.write(data)

        return oid