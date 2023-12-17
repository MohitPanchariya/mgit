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
        oid = data.hashObject(filepath)
        print(oid)
    except FileNotFoundError as exception:
        print(exception)

@app.command()
def cat_file(object_id):
    try:
        blob = data.getObject(object_id)
        sys.stdout.flush()
        sys.stdout.buffer.write(blob)
    except FileNotFoundError as exception:
        print(exception)


@app.command()
def write_tree():
    try:
        base.writeTree()
    except FileNotFoundError as exception:
        print(exception)

if __name__ == "__main__":
    app()