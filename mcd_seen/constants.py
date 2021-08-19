import os
from mcdreforged.api.types import ServerInterface

# Command prefixes
SEEN_PREFIX = '!!seen'
SEEN_TOP_PREFIX = '!!seen-top'
LIVER_TOP_PREFIX = '!!liver-top'
DEBUG_PREFIX = '!!liver'


def ensure(folder: str):
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return folder


# Seen file storage
DATA_FOLDER = ensure('config/seen')
CONFIG_FILE = os.path.join(DATA_FOLDER, 'config.json')
SEENS_FILE = os.path.join(DATA_FOLDER, 'seen.json')
LOG_FILE = os.path.join(DATA_FOLDER, 'player_seens.log')
SEENS_PATH_OLD = ['seen.json', 'config/seen.json']

# Plugin Metadata
META = ServerInterface.get_instance().get_plugin_metadata('mcd_seen')

# Debug mode
DEBUG_MODE = False
