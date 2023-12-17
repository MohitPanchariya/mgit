import data
import os


@data.mgit_required
def writeTree(directory = "."):
    '''
    This function is used to write a tree(directory) to the object 
    database.
    '''
    # Get the entries present in a directory
    directoryEntries = os.scandir(directory)

    for entry in directoryEntries:
        # Get the full path of an entry
        fullPath = os.path.join(directory, entry.name)
        if isIgnored(fullPath):
            continue
        if entry.is_file(follow_symlinks=False):
            print(fullPath)
            print(data.hashObject(fullPath))
        elif entry.is_dir(follow_symlinks=False):
            writeTree(fullPath)


def isIgnored(path):
    splitPath = os.path.split(path)
    if ".mgit" in splitPath[1]:
        return True
    return False