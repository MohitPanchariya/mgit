import data
import os
import textwrap


def init():
    '''
    This function is used to initialise a mgit repository.
    If the cwd is already a repository, an exception is raise.
    '''
    data.init()
    data.updateRef("HEAD", data.RefValue(symbolic=True, value=os.path.join(
        "ref", "heads", "master" 
    )))

@data.mgit_required
def getBranchName():
    try:
        HEAD = data.getRef("HEAD", deref=False)
    except FileNotFoundError:
        pass
    
    if not HEAD.symbolic:
        return None

    return os.path.relpath(HEAD.value, os.path.join("ref", "heads"))

@data.mgit_required
def commit(message):
    # check if HEAD is in detached state
    HEAD = data.getRef("HEAD", deref=False)
    detached = False
    if not HEAD.symbolic:
        print("HEAD is in a detached state.\n"\
            "Create a branch before switching to another branch "\
            "or checking out another commit to avoid losing "\
            "commits")
        detached = True
    
    # tree object-id
    commitObject = f"tree {writeTree()}\n"
    
    if detached:
        parent = data.getRef("HEAD", deref=False).value
    # Get the object-id pointed to by the branch
    else:
        parent = data.getRef(HEAD.value).value

    # parent commit hash
    if parent:
        commitObject += f"parent {parent}\n"
    # leaving a line between the metadata('tree' object-id) and the commit message
    commitObject += "\n"

    commitObject += message

    objectId = data.hashObject(commitObject.encode(), "commit")
    refValue = data.RefValue(symbolic=False, value=objectId)
    # If HEAD is detached, just update HEAD
    if detached:
        data.updateRef("HEAD", refValue)
    # If HEAD points to a branch, update the branch
    else:
        data.updateRef(HEAD.value, refValue, deref=False)
    return objectId

@data.mgit_required
def writeTree(directory = "."):
    '''
    This function is used to write a tree(directory) to the object 
    database.
    '''
    entries = []
    # Get the entries present in a directory
    directoryEntries = os.scandir(directory)

    for entry in directoryEntries:
        # Get the full path of an entry
        fullPath = os.path.join(directory, entry.name)
        if isIgnored(fullPath):
            continue
        if entry.is_file(follow_symlinks=False):
            type_ = "blob"
            name = entry.name
            with open(fullPath, "rb") as file:
                blob = file.read()

            oid = data.hashObject(blob)

            entries.append((type_, oid, name))

        elif entry.is_dir(follow_symlinks=False):
            type_ = "tree"
            name = entry.name
            oid = writeTree(fullPath)

            entries.append((type_, oid, name))

    tree = ""
    for entry in entries:
        tree += f"{entry[0]} {entry[1]} {entry[2]}\n"

    return data.hashObject(tree.encode(), type_= "tree")


@data.mgit_required
def readTree(objectId):
    if not os.path.exists(os.path.join(".mgit", "objects", objectId)):
        raise FileNotFoundError("No object found with given object-id.")
    _emptyDirectory()
    _createTree(objectId, basePath = "")

@data.mgit_required
def log(objectId = None):
    if not objectId:
        objectId = data.getRef("HEAD")

    while objectId:
        commit = data.getCommit(objectId)

        print(f"commit {objectId}")
        lines = textwrap.wrap(commit["message"])
        for line in lines:
            print(textwrap.indent(line, "   "))

        if "parent" in commit:
            objectId = commit["parent"]
        else:
            objectId = None

@data.mgit_required
def checkout(name):
    '''
    Checkout a branch.
    '''
    commitId = data.getOid(name)
    if isBranch(name):
        pointTo = os.path.join("ref", "heads", name)
        HEAD = data.RefValue(symbolic=True, value=pointTo)
    else:
        HEAD = data.RefValue(symbolic=False, value=commitId)
        print(f"HEAD is in a detached state at {commitId}")

    commit = data.getCommit(commitId)
    readTree(commit["tree"])
    data.updateRef("HEAD", HEAD , deref=False)


@data.mgit_required
def createTag(tag, commitId):
    if not os.path.exists(os.path.join(".mgit", "objects", commitId)):
        raise FileNotFoundError("No commit found with given commit id.")
    
    data.updateRef(os.path.join("ref", "tags", tag), data.RefValue(symbolic=False, value=commitId))


@data.mgit_required
def reset(commitId, hard = False):
    if not os.path.join(".mgit", "objects", commitId):
        raise FileNotFoundError("Commit with given commit id not found.")

    # Check if HEAD points to a branch
    currBranch = getBranchName()
    if not currBranch:
        raise Exception("HEAD doesn't point to a branch.\n"\
                        "A branch must be checked out before resetting.")
    
    # Make branch point to the give commit
    data.updateRef(
        os.path.join("ref", "heads", currBranch),
        data.RefValue(symbolic=False, value=commitId),
        deref=False
    )

    # If hard reset, revert the working directory back to the state
    # of the given commit
    if hard:
        commit = data.getCommit(commitId)
        tree = commit["tree"]
        readTree(tree)

@data.mgit_required
def isBranch(name):
    '''
    Returns True if provided name is a branch. Else
    returns false.
    '''
    try:
        _ = data.getRef(os.path.join("ref", "heads", name))
        return True
    except FileNotFoundError:
        return False


@data.mgit_required
def getBranches():
    for ref, _ in data.iterRefs(prefix=os.path.join("ref", "heads")):
        yield os.path.relpath(ref, os.path.join("ref", "heads"))

def _createTree(objectId, basePath):
    objectPath = os.path.join(".mgit", "objects", objectId)

    if not os.path.exists(objectPath):
        raise FileNotFoundError("Tree with given object id doesn't exist.")
    
    with open(objectPath, "rb") as file:
        treeObject = file.read()
    
    #Children array stores all the entries present in this tree object(its chidren)
    children = data.parseTreeObject(treeObject)
    
    for child in children:
        type_ = child["type_"]
        name = child["name"]
        oid = child["oid"]

        #If the object is a blob, create a file and write
        #the blob to the file
        if type_ == "blob":
            blob = data.getObject(oid, "blob")
            with open(os.path.join(basePath, name), "wb") as file:
                file.write(blob)
        elif type_ == "tree":
            os.makedirs(name, exist_ok = True)
            _createTree(
                objectId = oid, 
                basePath = os.path.join(basePath, name)
            )


def _emptyDirectory():
    '''
    Empty the current directory
    '''
    for root, dirnames, filenames in os.walk(".", topdown = False):
        for filename in filenames:
            path = os.path.join(root, filename)
            if isIgnored(path):
                continue
            
            print(path)
            os.remove(path)
        for dirname in dirnames:
            path = os.path.join(root, dirname)
            if isIgnored(path):
                continue

            try:
                print(path)
                os.rmdir(path)
            except (FileNotFoundError, OSError):
                # Since there are can be ignored files, in directories
                # the directory may not be empty and deletion might
                # fail which is the correct behaviour
                pass

def isIgnored(path):
    splitPath = os.path.split(path)
    for subPath in splitPath:
        if ".mgit" in subPath:
            return True
    return False