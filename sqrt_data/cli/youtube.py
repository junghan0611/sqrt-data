# [[file:../../org/youtube.org::*CLI][CLI:1]]
import click
from sqrt_data.parse import youtube as youtube_
# CLI:1 ends here

# [[file:../../org/youtube.org::*CLI][CLI:2]]
__all__ = ['youtube']

@click.group(help='YouTube stats')
def youtube():
    pass
# CLI:2 ends here

# [[file:../../org/youtube.org::*CLI][CLI:3]]
@youtube.command(help='Initialize the DB')
def init_db():
    youtube_.init_db()
# CLI:3 ends here

# [[file:../../org/youtube.org::*CLI][CLI:4]]
@youtube.command(help='Parse MPV logs')
@click.option('-c', '--confirm-missing', is_flag=True)
def parse_mpv(confirm_missing):
    youtube_.parse_mpv(confirm_missing)
# CLI:4 ends here

# [[file:../../org/youtube.org::*CLI][CLI:5]]
@youtube.command(help='Parse NewPipe logs')
def parse_newpipe():
    youtube_.parse_newpipe()
# CLI:5 ends here

# [[file:../../org/youtube.org::*CLI][CLI:6]]
@youtube.command(help='Parse YouTube logs')
def parse_youtube():
    youtube_.parse_youtube()
# CLI:6 ends here

# [[file:../../org/youtube.org::*CLI][CLI:7]]
@youtube.command(help='Create views')
def create_views():
    youtube_.create_views()
# CLI:7 ends here
