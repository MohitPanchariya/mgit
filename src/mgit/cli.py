import typer
import os
import sys
import data
import base
import subprocess
import textwrap

app = typer.Typer()

@app.command()
def init():
    try:
        base.init()
        print(f"Initialised repository in {os.path.join(os.getcwd())}")
    except FileExistsError as exception:
        print(exception)


@app.command()
def status():
    branch = base.getBranchName()

    if not branch:
        print(f"HEAD in detached mode at {data.getOid('HEAD')}")   
    else:
        print(f"On branch {branch}") 

@app.command()
def status():
    branch = base.getBranchName()
    if not branch:
        print(f"HEAD in datached mode at {data.getOid('@')}")
    else:
        print(f"On branch {branch}")

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
def log(object_id = "@"):
    object_id = data.getOid(object_id)
    for oid in data.iterParentsAndCommits({object_id}):
        commit = data.getCommit(oid)
        print(f"commit {oid}")
        lines = textwrap.wrap(commit["message"])
        for line in lines:
            print(textwrap.indent(line, "   "))

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
        if "parent" in commit:
            dot += f'"{oid}" -> "{commit["parent"]}"\n'
    
    dot += '}'

    with subprocess.Popen (
        ['dot', '-Tx11', '/dev/stdin'],
        stdin=subprocess.PIPE) as proc:
        proc.communicate (dot.encode ())


@app.command()
def branch(name, start_point = "@"):
    start_point = data.getOid(start_point)
    data.createBranch(name, start_point)
    print(f"Branch {name} created at {start_point}")

if __name__ == "__main__":
    app()