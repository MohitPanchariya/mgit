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
        base.readTree(tree_object_id)
    except FileNotFoundError as exception:
        print(exception)

@app.command()
def commit(message):
    try:
        print(base.commit(message))
    except Exception as exception:
        print(exception)

if __name__ == "__main__":
    app()