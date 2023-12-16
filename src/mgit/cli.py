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
        

if __name__ == "__main__":
    app()