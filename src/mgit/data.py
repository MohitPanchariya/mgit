import os
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
def hashObject(data, type_ = "blob"):
    '''
    This function is used to create an object and store in the
    object database of the mgit repository. 
    By default, the type is assumed to be blob.
    '''

    # Add type tag
    data = type_.encode() + b"\x00" + data
    # oid => object id
    oid = hashlib.sha1(data).hexdigest()
    # Create a blob object in the object database
    with open(os.path.join(os.getcwd(), MGIT_DIR, "objects", oid), "wb") as file:
        file.write(data)

    return oid


@mgit_required
def getObject(objectId, expected = "blob"):
    '''
    This function takes in an object id(sha1 hash) and returns the
    content of the object.
    '''
    if not os.path.exists(os.path.join(MGIT_DIR, "objects", objectId)):
        raise FileNotFoundError("No object found with given object id.")
    else:
        with open(os.path.join(MGIT_DIR, "objects", objectId), "rb") as file:
            object = file.read()
        
        type_, _, data = object.partition(b"\x00")
        type_ = type_.decode ()

        if expected is not None:
            assert type_ == expected, f'Expected {expected}, got {type_}'
        return data
    

@mgit_required
def setHead(objectId):
    with open(os.path.join(MGIT_DIR, "HEAD"), "w") as file:
        file.write(objectId)


@mgit_required
def getHead():
    head = None
    headPath = os.path.join(MGIT_DIR, "HEAD")
    if os.path.exists(headPath):
        with open(headPath, "r") as file:
            head = file.read().strip()
    return head

def parseTreeObject(treeObj):
    #Get the data of the tree object
    type_, _, data = treeObj.partition(b"\x00")

    if type_ != b"tree":
        raise Exception(f"Expected a tree object. Received: {type_}")
    
    #Entries will store the tokenised data
    #Each element in the children array is a dictionary, 
    #which consists of type of object, object id and object name
    children = []

    for line in data.splitlines():
        words = line.split()
        children.append({
            "type_": words[0].decode(), "oid": words[1].decode(), "name": words[2].decode()
        })

    return children