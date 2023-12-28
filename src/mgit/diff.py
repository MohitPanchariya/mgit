from collections import defaultdict
import base

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

        
def diffTrees(fromTree, toTree):
    '''
    returns a string which lists the files that have 
    changed across the given trees.
    '''
    diff = ""
    for path, fromOid, toOid in groupTrees(fromTree, toTree):
        if fromOid != toOid:
            diff += f'changed: {path}\n'
    return diff