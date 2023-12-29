import typer
import os
import sys
import data
import base
import subprocess
import textwrap
import diff as myDiff

app = typer.Typer()

@app.command()
def init():
    try:
        base.init()
        print(f"Initialised repository in {os.path.join(os.getcwd())}")
    except FileExistsError as exception:
        print(exception)

@app.command()
def hash_object(filepath):
    try:
        with open(filepath, "rb") as file:
            object = file.read()
        
        oid = data.hashObject(object)
        print(oid)
    except FileNotFoundError as exception:
        print(exception)

@app.command()
def cat_file(object_id, type = "blob"):
    try:
        # Allows user to pass a reference or an object id
        object_id = data.getOid(object_id)
        blob = data.getObject(object_id, expected = type)
        sys.stdout.flush()
        sys.stdout.buffer.write(blob)
    except FileNotFoundError as exception:
        print(exception)


@app.command()
def write_tree():
    try:
        oid = base.writeTree()
        print(oid)
    except FileNotFoundError as exception:
        print(exception)

@app.command()
def read_tree(tree_object_id):
    try:
        # Allows user to pass a reference or an tree object id
        tree_object_id = data.getOid(tree_object_id)
        base.readTree(tree_object_id)
    except FileNotFoundError as exception:
        print(exception)

@app.command()
def commit(message):
    try:
        print(base.commit(message))
    except Exception as exception:
        print(exception)

@app.command()
def diff(commit_id = "HEAD"):
    workingTree = base.getWorkingTree()

    objectId = data.getOid(commit_id)
    commit = data.getCommit(objectId)
    tree = base.getTree(commit["tree"])
    
    output = myDiff.diffTrees(tree, workingTree, True)
    for change in output:
        print(f"File changed: {change}")
        for line in output[change]:
            print(line)

@app.command()
def status():
    branch = base.getBranchName()

    if not branch:
        print(f"HEAD in detached mode at {data.getOid('HEAD')}")   
    else:
        print(f"On branch {branch}") 

    MERGE_HEAD = None

    try:
        MERGE_HEAD = data.getRef('MERGE_HEAD').value
    except Exception:
        pass

    if MERGE_HEAD:
        print (f'Merging with {MERGE_HEAD[:10]}')
    
    workingTree = base.getWorkingTree()

    objectId = data.getOid("HEAD")
    commit = data.getCommit(objectId)
    tree = base.getTree(commit["tree"])

    for path, action in myDiff.iterChangedFiles(tree, workingTree):
        print(f"File action: {path} ({action})")


@app.command()
def merge(branch_name):
    base.merge(branch_name)

def _printCommit(oid, ref = None):
    commit = data.getCommit(oid)
    printStr = f"commit {oid}"
    if ref:
        printStr += f", (tag: {ref})"
    print(printStr)
    lines = textwrap.wrap(commit["message"])
    for line in lines:
        print(textwrap.indent(line, "   "))

@app.command()
def log(object_id = "@"):
    # Fetch all tags and create a reverse look up(commitId->tag)
    lookUp = {}
    for tag, commitId in data.iterRefs(prefix=os.path.join("ref", "tags")):
        lookUp[commitId.value] = os.path.relpath(tag, os.path.join("ref", "tags"))

    if object_id == "@":
        object_id = data.getRef("HEAD", deref=True).value
    else:
        object_id = data.getOid(object_id)

    for oid in data.iterParentsAndCommits({object_id}):
        if oid in lookUp:
            _printCommit(oid, lookUp[oid])
        else:
            _printCommit(oid)


@app.command()
def show(commit_id, unified_diff: bool = False):
    _printCommit(commit_id)
    commit = data.getCommit(commit_id)
    
    tree = base.getTree(commit["tree"])
    parentTree = None
    if "parents" in commit:
        if commit["parents"] != []:
            parentCommit = data.getCommit(commit["parents"][0])
            parentTree = base.getTree(parentCommit["tree"])

    output = myDiff.diffTrees(parentTree, tree, unified_diff)
    for change in output:
        print(f"File changed: {change}")
        if unified_diff:
            for line in output[change]:
                print(line)

@app.command()
def checkout(name):
    # Allows user to pass a reference or a commit id
    base.checkout(name)

@app.command()
def tag(name, commit_id = None):
    try:
        if not commit_id:
            commit_id = data.getRef("HEAD").value
        base.createTag(name, commit_id)
    except Exception as execption:
        print(execption)


@app.command()
def k():
    dot = 'digraph commits {\n'
    oids = set()
    # populate oids with the oids of the refs
    for refname, ref in data.iterRefs(deref=False):
        dot += f'"{refname}" [shape=note]\n'
        dot += f'"{refname}" -> "{ref.value}"\n'
        if not ref.symbolic:
            oids.add(ref.value)

    # Print all commits that can be reached through the
    # oids of the refs
    for oid in data.iterParentsAndCommits(oids):
        commit = data.getCommit(oid)
        dot += f'"{oid}" [shape=box style=filled label="{oid[:10]}"]\n'
        if "parents" in commit:
            for parent in commit["parents"]:
                dot += f'"{oid}" -> "{parent}"\n'
    
    dot += '}'

    with subprocess.Popen (
        ['dot', '-Tx11', '/dev/stdin'],
        stdin=subprocess.PIPE) as proc:
        proc.communicate (dot.encode ())


@app.command()
def branch(name = "", start_point = "HEAD", list:bool = False):
    if list:
        currentBranch = base.getBranchName()
        for branch in base.getBranches():
            prefix = "*" if branch == currentBranch else " "
            print(f"{prefix} {branch}")
    else:
        if name == "":
            print("A name must be provided.")
            sys.exit(1)
        start_point = data.getOid(start_point)
        data.createBranch(name, start_point)
        print(f"Branch {name} created at {start_point}")


@app.command()
def reset(commit_id, hard: bool = False):
    try:
        base.reset(commit_id, hard)
    except Exception as exception:
        print(exception)

if __name__ == "__main__":
    app()