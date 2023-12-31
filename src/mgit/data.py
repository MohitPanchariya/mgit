import os
import hashlib
import string
from collections import deque, namedtuple

MGIT_DIR = "./.mgit"

RefValue = namedtuple("RefValue", ["symbolic", "value"])


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
        os.makedirs(os.path.join(MGIT_DIR, "ref", "heads"))
        # create master branch on init
        with open(os.path.join(MGIT_DIR, "ref", "heads", "master"), "w"):
            pass

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
    objectId = getOid(objectId)
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
def updateRef(reference, refValue, deref = True):
    '''
    Update a reference to point to the given RefValue(refValue).
    If reference doesn't exist, a reference is created.
    Note: The reference must be a relative path from the
    .mgit directory. 
    E.g: To create a tag named "example", the reference
    passed in as an argument must be, "ref/tags/example".
    The reference is created in, ".mgit/ref/tags/example".
    '''
    refPath = os.path.join(MGIT_DIR, reference)
    os.makedirs(os.path.dirname(refPath), exist_ok=True)

    # create the reference file
    if not os.path.exists(refPath):
        open(refPath, "w")
        
    reference = _getRefInternal(reference, deref)[0]
    # If deref is set to true, refPath needs to be updated
    # to the reference being pointed to
    if deref:
        refPath = os.path.join(MGIT_DIR, reference)
    assert refValue.value
    if refValue.symbolic:
        refValue = f"ref: {refValue.value}"
    else:
        refValue = refValue.value
        

    with open(refPath, "w") as file:
        file.write(refValue)


@mgit_required
def getRef(reference, deref = True):
    '''
    Returns the object-id pointed to by the given reference.
    If a reference points to another reference(a symbolic ref), 
    the references are recursively tracked down and the object id 
    the last reference points to is returned.
    Note: The reference must be a relative path from the
    .mgit directory. 
    E.g: To create a tag named "example", the reference
    passed in as an argument must be, "ref/tags/example".
    The reference is created in, ".mgit/ref/tags/example".
    '''
    return _getRefInternal(reference, deref)[1]

@mgit_required
def _getRefInternal(reference, deref):
    '''
    Returns a reference name and a RefValue named tuple. 
    If a reference points to another reference(a symbolic ref), 
    the references are recursively tracked down and the reference
    of the last oid, and a RefValue are returned.
    Note: The reference must be a relative path from the
    .mgit directory. 
    E.g: To create a tag named "example", the reference
    passed in as an argument must be, "ref/tags/example".
    The reference is created in, ".mgit/ref/tags/example".
    '''
    refPath = os.path.join(MGIT_DIR, reference)
    value = None
    if not os.path.exists(refPath):
        raise FileNotFoundError("No reference found with given path.")
    
    with open(refPath, "r") as file:
        value = file.read().strip()

    symbolic = bool (value) and value.startswith("ref:")
    if symbolic:
        value = value.split(":", 1)[1].strip()
        if deref:
            return _getRefInternal(value, deref)
    
    return reference, RefValue(symbolic=symbolic, value=value)

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
            return getRef(ref, deref=False).value
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
def iterRefs(prefix = "", deref = True):
    '''
    Iterates over all the references, return a reference name and
    the reference(object-id).
    '''
    refs = ["HEAD"]
    if os.path.exists(os.path.join(MGIT_DIR, "MERGE_HEAD")):
        refs.append("MERGE_HEAD")
    # Walk over all refs
    for root, _, filenames in os.walk(os.path.join(MGIT_DIR, "ref")):
        root = os.path.relpath(root, MGIT_DIR)

        for file in filenames:
            refs.append(os.path.join(root, file))

    for refname in refs:
        if not refname.startswith(prefix):
            continue
        ref = getRef(refname, deref=deref)
        yield refname, ref


@mgit_required
def iterParentsAndCommits(oids):
    '''
    A generator which returns all the parents and commits
    reachable from a given set of object-ids.
    Note: Even if an object is reachable from multiple commits, 
    its returned only once.
    '''
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
        if "parents" in commit:
            parents = commit["parents"]
        else:
            parents = []
        
        # Add first parent next
        oids.extendleft(parents[:1])
        # Add other parents later
        oids.extend(parents[1:])
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
    commit["parents"] = []

    lines = iter(data.splitlines())

    for line in lines:
        if line == "":
            break
        key, value = line.split(" ", 1)
        if key == "tree":
            commit["tree"] = value
        elif key == "parent":
            commit["parents"].append(value)
        else:
            raise Exception(f"Unknow Key found: {key}")
    
    commit["message"] = "\n".join(lines)

    return commit

def deleteRef(ref, deref=True):
    ref = _getRefInternal(ref, deref)[0]
    os.remove(os.path.join(MGIT_DIR, ref))

@mgit_required
def createBranch(branchName, startPoint):
    '''
    Create a branch with the give branchName and startPoint
    (object-id)
    '''
    updateRef(os.path.join("ref", "heads", branchName), RefValue(symbolic=False, value=startPoint))

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