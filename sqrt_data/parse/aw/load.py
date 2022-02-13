# [[file:../../../org/aw.org::*Loading (Dekstop)][Loading (Dekstop):1]]
import furl
import tldextract
import glob
import pandas as pd
import os
import re
import logging

from sqlalchemy.dialects.postgresql import insert
from tqdm import tqdm

from sqrt_data.api import settings, DBConn, HashDict
from sqrt_data.models import Base
from sqrt_data.models.aw import AfkStatus, CurrentWindow, AppEditor, WebTab
from sqrt_data.parse.locations import LocationMatcher
# Loading (Dekstop):1 ends here

# [[file:../../../org/aw.org::*Loading (Dekstop)][Loading (Dekstop):2]]
__all__ = ['load']
# Loading (Dekstop):2 ends here

# [[file:../../../org/aw.org::*Loading (Dekstop)][Loading (Dekstop):3]]
def get_dataframes(h):
    files = glob.glob(
        f'{os.path.expanduser(settings["aw"]["logs_folder"])}/*.csv'
    )
    dfs_by_type = {}
    files_by_type = {}
    for f in files:
        if not h.is_updated(f):
            continue
        try:
            df = pd.read_csv(f, lineterminator='\n', index_col=False)
        except pd.errors.ParserError:
            logging.error(f'Error parsing file: {f}')
            continue
        type_ = re.search(r'^\w+', os.path.basename(f)).group(0)
        try:
            dfs_by_type[type_].append(df)
            files_by_type[type_].append(f)
        except KeyError:
            dfs_by_type[type_] = [df]
            files_by_type[type_] = [f]
        h.save_hash(f)
    for type, files in files_by_type.items():
        print(f'Type: {type}')
        print('Files')
        print("\n".join(files))
    return dfs_by_type
# Loading (Dekstop):3 ends here

# [[file:../../../org/aw.org::*Loading (Dekstop)][Loading (Dekstop):4]]
MODELS = {
    'afkstatus': AfkStatus,
    'currentwindow': CurrentWindow,
    'app_editor_activity': AppEditor,
    'web_tab_current': WebTab
}
# Loading (Dekstop):4 ends here

# [[file:../../../org/aw.org::*Loading (Dekstop)][Loading (Dekstop):5]]
def get_records(type_, df):
    loc = LocationMatcher()
    if type_ == 'afkstatus':
        df['status'] = df['status'] == 'not-afk'
    if type_ == 'currentwindow':
        df['app'] = df['app'].apply(
            lambda app: settings['aw']['apps_convert'].get(app, app)
        )
    if type_ == 'web_tab_current':
        df = df.rename({'tabCount': 'tab_count'}, axis=1)
        df['site'] = [
            tldextract.extract(url).registered_domain
            for url in df['url']
        ]
        df['url_no_params'] = [
            furl.furl(url).remove(args=True, fragment=True).url
            for url in df['url']
        ]
    if type_ == 'app_editor_activity':
        if 'branch' in df.columns:
            df = df.drop('branch', axis=1)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    locations = df.apply(
        lambda row: loc.get_location(row.timestamp, row.hostname), axis=1
    )
    df['location'] = [l[0] for l in locations]
    df['timestamp'] = [l[1] for l in locations]
    return df.to_dict(orient='records')
# Loading (Dekstop):5 ends here

# [[file:../../../org/aw.org::*Loading (Dekstop)][Loading (Dekstop):6]]
def load():
    DBConn()
    DBConn.create_schema('aw', Base)
    with HashDict() as h:
        dfs_by_type = get_dataframes(h)

        with DBConn.get_session() as db:
            for type_, dfs in tqdm(dfs_by_type.items()):
                for df in dfs:
                    entries = get_records(type_, df)
                    db.execute(insert(MODELS[type_]).values(entries).on_conflict_do_nothing())
            db.commit()
        h.commit()
# Loading (Dekstop):6 ends here
