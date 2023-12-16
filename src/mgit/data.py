import os
import sys
import hashlib

MGIT_DIR = "./.mgit"

def mgit_required(func):
    '''
    This decorator is used to make sure the mgit directory exists.
    '''
    def wrapper(*args, **kwargs):
        if not os.path.exists(MGIT_DIR):
            raise FileNotFoundError("This is not a mgit repository."\
                                "Use the mgit init command to make this a git repository.")
        else:
            return func(*args, **kwargs)
            
    return wrapper


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

@mgit_required
def hashObject(filePath):
    '''
    This function is used to create a blob object and store in the
    object database of the mgit repository. 
    '''
    with open(filePath, "rb") as file:
        data = file.read()
    
    # oid => object id
    oid = hashlib.sha1(data).hexdigest()
    # Create a blob object in the object database
    with open(os.path.join(os.getcwd(), MGIT_DIR, "objects", oid), "wb") as file:
        file.write(data)

    return oid


@mgit_required
def catFile(obejctId):
    '''
    This function takes in an object id(sha1 hash) and prints out
    the content of that blob object
    '''
    if not os.path.exists(os.path.join(MGIT_DIR, "objects", obejctId)):
        raise FileNotFoundError("No blob object found with given object id.")
    else:
        sys.stdout.flush()
        with open(os.path.join(MGIT_DIR, "objects", obejctId), "rb") as blob:
            return blob.read()