import os
import sys
import logging

import pandas as pd
from tqdm import tqdm

from sqrt_data.api import is_updated, save_hash, DBConn, Config
from sqrt_data.models import Base, MpdSong

__all__ = ['load_library']


def load_library():
    csv_path = os.path.expanduser(Config.MPD_CSV)
    if not is_updated(csv_path):
        logging.info('MPD library already saved, skipping')
        sys.exit(0)
    logging.info('Saving MPD Library')
    df = pd.read_csv(csv_path)
    DBConn()
    DBConn.create_schema('mpd', Base)

    with DBConn.get_session() as db:
        tracks = list(df.itertuples(index=False))
        for track in tqdm(tracks):
            track = track._asdict()
            song = MpdSong(**{k:v for k, v in track.items() if k in MpdSong.__table__.columns.keys()})

            added = db.query(MpdSong).filter_by(file=track['file']).first()
            if not added:
                db.merge(song)
        db.commit()
    save_hash(csv_path)


if __name__ == "__main__":
    load_library()
