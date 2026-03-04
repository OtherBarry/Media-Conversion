from typer import Typer

from .convert import convert
from .convert_directory import convert_directory
from .convert_all import convert_all

app = Typer(name="Transcoder")

app.command()(convert)
app.command()(convert_directory)
app.command()(convert_all)
