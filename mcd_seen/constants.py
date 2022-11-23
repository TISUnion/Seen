import os


def ensure(folder: str):
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return folder


# Seen file storage
DATA_FOLDER = ensure('config/seen')
CONFIG_FILE = os.path.join(DATA_FOLDER, 'config.json')
SEENS_FILE = os.path.join(DATA_FOLDER, 'seen.json')
LOG_FILE = os.path.join(DATA_FOLDER, 'logs', 'seen.log')
SEENS_PATH_OLD = ['seen.json', 'config/seen.json']
OLD_LOG_FILE = os.path.join(DATA_FOLDER, 'player_seens.log')
NEW_LOG_PATH = os.path.join(DATA_FOLDER, 'logs', 'old_seens.log')
