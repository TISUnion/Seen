import logging
import time
import types
import re
import os

from typing import Optional
from mcdreforged.api.types import MCDReforgedLogger, PluginServerInterface
from mcdreforged.api.rtext import *

from mcd_seen.constants import LOG_FILE, META, DEBUG_MODE
from mcd_seen.config import config


class SeenLogger(MCDReforgedLogger):
    __global_instance = None    # type: Optional[PluginServerInterface]

    def debug(self, *args, **kwargs):
        if DEBUG_MODE:
            super(MCDReforgedLogger, self).debug(*args, **kwargs)

    def set_file(self, file_name: str):
        if self.file_handler is not None:
            self.removeHandler(self.file_handler)
        if not os.path.isfile(LOG_FILE):
            with open(LOG_FILE, 'w') as f:
                f.write('')
        self.file_handler = logging.FileHandler(file_name, encoding='UTF-8')
        self.file_handler.setFormatter(self.FILE_FMT)
        self.addHandler(self.file_handler)

    @classmethod
    def inject(cls, server: PluginServerInterface) -> None:
        server.logger.set_file = types.MethodType(cls.set_file, server.logger)
        server.logger.debug = types.MethodType(cls.set_file, server.logger)
        server.logger.set_file(LOG_FILE)
        cls.__global_instance = server

    @classmethod
    def get_server(cls) -> PluginServerInterface:
        if cls.__global_instance is None:
            cls.inject(PluginServerInterface.get_instance().as_plugin_server_interface())
        return cls.__global_instance

    @classmethod
    def get_instance(cls) -> MCDReforgedLogger:
        if cls.__global_instance is None:
            cls.inject(PluginServerInterface.get_instance().as_plugin_server_interface())
        return cls.__global_instance.logger


logger = SeenLogger.get_instance()


def log_seen(msg: str, *args, **kwargs):
    if config.log_seens:
        logger.info(msg, *args, **kwargs)


def rclick(msg: str, hover: str, cmd: str, action: RAction = RAction.run_command,
           color: Optional[RColor] = None, style: Optional[RStyle] = None) -> RText:
    return RText(msg, color, style).h(hover).c(action, cmd)


def verify_player_name(name: str) -> bool:
    return re.fullmatch(r'\w+', name) is not None


def tr(key: str, *fmt, lang: str = None):
    if not key.startswith(f'{META.id}.'):
        key = f'{META.id}.{key.strip(".")}'
    return SeenLogger.get_server().tr(key, *fmt, language=lang)


def formatted_time(t: int or str):
    t = int(t)
    values = []
    units = tr("mcd_seen.fmt.delta_time").split(' ')
    scales = [60, 60, 24]
    for scale in scales:
        value = t % scale
        values.append(value)

        t //= scale
        if t == 0:
            break
    if t != 0:
        # Time large enough
        values.append(t)

    s = ""
    for i in range(len(values)):
        value = values[i]
        unit = units[i]
        s = "{v} {u} ".format(v=value, u=unit) + s
    return f'§6{s.strip()}'


def now_time() -> int:
    return int(time.time())


def delta_time(last_seen: int) -> int:
    return now_time() - abs(last_seen)


def bot_name(player: str):
    return player + '@bot'


def is_bot(name: str) -> bool:
    name = name.upper()
    blacklist = 'A_Pi#nw#sw#SE#ne#nf#SandWall#storage#Steve#Alex#DuperMaster#Nya_Vanilla#Witch#Klio_5#######'.upper()
    black_keys = [r'farm', r'bot_', r'cam', r'_b_', r'bot-', r'bot\d', r'^bot']
    if blacklist.find(name) >= 0 or len(name) < 4 or len(name) > 16:
        return True
    for black_key in black_keys:
        if re.search(black_key.upper(), name):
            return True
    return False
