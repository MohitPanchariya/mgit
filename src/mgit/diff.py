from collections import defaultdict
import base
import data
import difflib

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

    for i, treeId in enumerate(trees):
        tree = base.getTree(treeId)
    
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