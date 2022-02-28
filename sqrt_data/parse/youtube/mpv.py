import glob
import json
import re
import pandas as pd
import sqlalchemy as sa
from dateutil import parser

from sqrt_data.models.youtube import Watch
from sqrt_data.api import HashDict, DBConn, settings

from .api import get_video_by_id, get_video_id, store_logs

__all__ = ['parse_mpv']

def process_log(filename):
    with open(filename, 'r') as f:
        contents = f.read()

    events = [c for c in contents.split('\n') if len(c) > 0]
    res = []
    current_video = None
    prev_event = None
    acc_duration = 0
    for datum in events:
        try:
            event = json.loads(datum)
        except:
            print(f'Cannot parse: {datum}')
            continue

        if 'kind' not in event or 'time' not in event:
            continue

        time = parser.parse(event['time'])

        if event['kind'] == 'loaded' and 'youtube.com' in event['path']:
            current_video = get_video_id(event['path'])
            if current_video:
                acc_duration, prev_event = 0, event

        if current_video is None:
            continue

        if event['kind'] == 'stop' or event['kind'] == 'end':
            if prev_event['kind'] != 'pause':
                prev_time = parser.parse(prev_event['time'])
                acc_duration += (time - prev_time).total_seconds()
            res.append(
                {
                    'video_id': current_video,
                    'date': time.date().isoformat(),
                    'kind': 'mpv',
                    'duration': acc_duration
                }
            )
            current_video, prev_event, acc_duration = None, None, 0

        if event['kind'] in ['seek', 'pause', 'play']:
            if prev_event['kind'] != 'pause':
                prev_time = parser.parse(prev_event['time'])
                acc_duration += (time - prev_time).total_seconds()
            if event['kind'] != 'pause':
                prev_event = event

    if current_video:
        print(f'Error in {filename}')

    return res, current_video is None

def parse_mpv(confirm_missed):
    files = glob.glob(f'{settings["youtube"]["mpv_folder"]}/*.log')
    DBConn()
    with DBConn.get_session() as db:
        with HashDict() as h:
            for f in files:
                if h.is_updated(f):
                    logs, is_ok = process_log(f)
                    if is_ok and len(logs) > 0:
                        print(f)
                        missed = store_logs(logs, db)
                        if not missed or confirm_missed:
                            h.save_hash(f)
                db.commit()
                h.commit()
