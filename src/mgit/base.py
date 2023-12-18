import data
import os


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

def isIgnored(path):
    splitPath = os.path.split(path)
    if ".mgit" in splitPath[1]:
        return True
    return False