import typer
import os
import data

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

if __name__ == "__main__":
    app()