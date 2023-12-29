from collections import defaultdict
import data
import difflib
from tempfile import NamedTemporaryFile as Temp
import subprocess

def diffBlobs(blobId1, blobId2):
    '''
    Returns the unified difference between two blobs
    '''
    blob1 = []
    blob2 = []
    if blobId1:
        blob1 = data.getObject(blobId1).decode().splitlines()
    if blobId2:
        blob2 = data.getObject(blobId2).decode().splitlines()
    
    diff = []
    for line in difflib.unified_diff(blob1, blob2):
        diff.append(line)
    
    return diff

def groupTrees(*trees):
    '''
    Group the given trees by file paths and their oids
    across different commits.
    The function yields a file path along with a list of
    object ids for the file in the given list of trees.
    The entries in the list are ordered in the order of trees.
    If a file didn't exist during a particular commit, its
    oids in the list is set to None.
    '''
    entries = defaultdict(lambda: [None] * len(trees))

    for i, tree in enumerate(trees):
        if tree:
            for path, oid in tree.items():
                entries[path][i] = oid

    for path, oids in entries.items():
        yield (path, *oids)

        
def diffTrees(fromTree, toTree, unifiedDiff = False):
    '''
    returns a string which lists the files that have 
    changed across the given trees.
    '''
    diff = {}
    for path, fromOid, toOid in groupTrees(fromTree, toTree):
        if fromOid != toOid:
            diff[path] = None
            if unifiedDiff:
                diff[path] = diffBlobs(fromOid, toOid)
    
    return diff


def iterChangedFiles(fromTree, toTree):
    '''
    Yields an action(modified, new file, deleted, unchanged) for 
    each file in the given trees.
    '''
    for path, fromOid, toOid in groupTrees(fromTree, toTree):
        if not fromOid:
            action = "New File"
        elif not toOid:
            action = "Deleted"
        elif fromOid != toOid:
            action = "Modified"
        else:
            action = "Unchanged"
        yield path, action


def mergeTrees(t_HEAD, t_other):
    '''
    Takes in two tree objects and returns back a tree object
    with merged data of the files.
    '''
    tree = {}
    for path, o_HEAD, o_other in groupTrees(t_HEAD, t_other):
        tree[path] = mergeBlobs(o_HEAD, o_other)
    return tree


def mergeBlobs(o_HEAD, o_other):
    '''
    Returns a merged blob.
    '''
    # create temp files as the diff subprocess needs
    # files to work with
    with Temp () as f_HEAD, Temp () as f_other:
        for oid, f in ((o_HEAD, f_HEAD), (o_other, f_other)):
            if oid:
                f.write (data.getObject(oid))
                f.flush ()

        with subprocess.Popen (
            ['diff',
             '-DHEAD', f_HEAD.name,
             f_other.name
            ], stdout=subprocess.PIPE) as proc:
            output, _ = proc.communicate ()

        return output