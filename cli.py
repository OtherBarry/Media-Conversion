from interfaces.cli import app as cli
from transcoder.events import on_startup, on_shutdown

if __name__ == "__main__":
    on_startup()
    cli()
    on_shutdown()
