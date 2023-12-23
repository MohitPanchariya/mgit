import os
import hashlib
import string
from collections import deque

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
def updateRef(reference, objectId):
    '''
    Update a reference to point to the given objectId.
    If reference doesn't exist, a reference is created.
    Note: The reference must be a relative path from the
    .mgit directory. 
    E.g: To create a tag named "example", the reference
    passed in as an argument must be, "ref/tags/example".
    The reference is created in, ".mgit/ref/tags/example".
    '''
    refPath = os.path.join(MGIT_DIR, reference)
    os.makedirs(os.path.dirname(refPath), exist_ok=True)

    with open(refPath, "w") as file:
        file.write(objectId)


@mgit_required
def getRef(reference):
    refPath = os.path.join(MGIT_DIR, reference)
    if not os.path.exists(refPath):
        raise FileNotFoundError("No reference found with given path.")
    
    with open(refPath, "r") as file:
        ref = file.read().strip()
    return ref

@mgit_required
def getOid(name):
    '''
    Returns the object-id associated with the tag.
    If the tag is an object-id, the tag itself it returned.
    '''
    if name == "@":
        name = "HEAD"
    # Search for the provided tag in the following directories
    # This way, the search for the reference will happen in
    # .mgit directory(user specifies ref/tags/tag)
    # .mgit/ref directory(user specifies tags/tag)
    # .mgit/ref/teags directory(user specifies tag)
    # .mgit/ref/heads
    refsToTry = [
        name,
        os.path.join("ref", name),
        os.path.join("ref", "tags", name),
        os.path.join("ref", "heads", name)
    ]

    for ref in refsToTry:
        try:
            return getRef(ref)
        except Exception:
            continue

    # If no ref has been found for the give name, name might be an oid
    # Name is SHA1
    is_hex = all (c in string.hexdigits for c in name)
    if len (name) == 40 and is_hex:
        return name
    
    # If the name isn't an oid either, raise an exception
    raise Exception("Object-id not found for the given name.")


@mgit_required
def iterRefs():
    '''
    Iterates over all the references, return a reference name and
    the reference(object-id).
    '''
    refs = ["HEAD"]
    # Walk over all refs
    for root, _, filenames in os.walk(os.path.join(MGIT_DIR, "ref")):
        root = os.path.relpath(root, MGIT_DIR)

        for file in filenames:
            refs.append(os.path.join(root, file))

    for refname in refs:
        yield refname, getRef(refname)


@mgit_required
def iterParentsAndCommits(oids):
    '''
    A generator which returns all the parents and commits
    reachable from a given set of object-ids.
    Note: Even if an object is reachable from multiple commits, 
    its returned only once.
    '''
    # Get rid of any duplicate oids
    oids = deque(oids)
    visited = set()

    while oids:
        oid = oids.popleft()
        # if not oid is needed as the previous oid may not have 
        # a parent
        if not oid or oid in visited:
            continue

        visited.add(oid)

        commit = getCommit(oid)
        if "parent" in commit:
            parent = commit["parent"]
        else:
            parent = None
        
        oids.appendleft(parent)
        yield oid

def getCommit(objectId):
    '''
    This function returns a dictionary representing a commit object.
    commit = {
        tree: object-id of the tree,
        parent: object-id of the previous commit, if it exists,
        message: The commit message
    }
    '''
    data = getObject(objectId, expected = "commit").decode()

    commit = {}

    lines = iter(data.splitlines())

    for line in lines:
        if line == "":
            break
        key, value = line.split(" ", 1)
        if key == "tree":
            commit["tree"] = value
        elif key == "parent":
            commit["parent"] = value
        else:
            raise Exception(f"Unknow Key found: {key}")
    
    commit["message"] = "\n".join(lines)

    return commit

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