import typer
import os
import sys
import data
import base

app = typer.Typer()

@app.command()
def init():
    try:
        data.init()
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
def log(object_id = None):
    if object_id:
        # Allows user to pass a reference or an object id
        object_id = data.getOid(object_id)
    base.log(object_id)

@app.command()
def checkout(commit_id):
    # Allows user to pass a reference or a commit id
    commit_id = data.getOid(commit_id)
    base.checkout(commit_id)

@app.command()
def tag(name, commit_id = None):
    try:
        if not commit_id:
            commit_id = data.getRef("HEAD")
        base.createTag(name, commit_id)
    except Exception as execption:
        print(execption)


if __name__ == "__main__":
    app()