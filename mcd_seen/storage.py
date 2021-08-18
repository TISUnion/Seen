import os
import json
import time
import shutil

from typing import Dict, List, Iterable, Optional

from mcdreforged.api.decorator import new_thread
from mcdreforged.api.utils import Serializable

from mcd_seen.constants import SEENS_FILE, META, SEENS_PATH_OLD
from mcd_seen.utils import now_time, log_seen, logger, bot_name, is_bot
from mcd_seen.config import config

bot_list = []


class PlayerSeen(Serializable):
    name: str
    joined: int = 0
    left: int = 0

    def __init__(self, name: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    @property
    def online(self):
        return self.joined > self.left

    def join(self):
        self.joined = now_time()

    def leave(self):
        self.left = now_time()
        if self.joined == 0:
            self.joined = now_time() - 1

    @property
    def actual_name(self):
        return self.name[:-4] if self.is_bot else self.name

    @property
    def is_bot(self):
        return self.name.endswith('@bot')

    @property
    def target(self) -> int:
        return self.joined if self.online else self.left

    def serialize(self) -> dict:
        ret = super().serialize()
        ret.pop('name')
        return ret

    @property
    def is_empty(self):
        return self.joined == self.left == 0


class SeenStorage:
    def __init__(self):
        self.data = {}      # type: Dict[str, PlayerSeen]

    @new_thread(META.name + '_PlayerJoin')
    def player_joined(self, name: str, save=True):
        self[name].join()
        log_seen(f'Player {name} joined the game')
        if self.is_bot(name):
            time.sleep(config.bot_list_delay)
            bot_list.append(name)
        if save:
            self.save()

    @new_thread(META.name + '_PlayerLeft')
    def player_left(self, name: str, save=True):
        if bot_name(name) in bot_list:
            name = bot_name(name)
            bot_list.remove(name)
        self[name].leave()
        log_seen(f'Player {name} left the game')
        if save:
            self.save()

    @new_thread(META.name + '_Debug')
    def debug_remove(self, players: Iterable[str]):
        removed = []
        for p in players:
            result = self.data.pop(p, None)
            if result is not None:
                removed.append(p)
        logger.debug(f"Removed {len(removed)} players' data: {', '.join(removed)}")

    @staticmethod
    def is_bot(name: str) -> bool:
        return name.endswith('@bot')

    def save(self):
        to_save = {}
        for p, s in self.data.items():
            if not s.is_empty:
                to_save[p] = s.serialize()
        with open(SEENS_FILE, 'w', encoding='UTF-8') as f:
            json.dump(to_save, f, ensure_ascii=False)

    def load(self):
        self.data = {}
        need_convert = False
        if not os.path.isfile(SEENS_FILE):
            for f in SEENS_PATH_OLD:
                if os.path.isfile(f):
                    shutil.move(f, SEENS_FILE)
                    need_convert = True
                    break
            if not need_convert:
                self.save()
        with open(SEENS_FILE, 'r', encoding='UTF-8') as f:
            to_load = json.load(f)
        for p, s in to_load.copy().items():
            to_des = s.copy()
            pl = p
            if need_convert and is_bot(p):
                pl = bot_name(p)
            to_des['name'] = pl
            self.data[pl] = PlayerSeen.deserialize(to_des)
        return self

    def seen_top(self, bot=False, _all=False):
        to_sort = []        # type: List[PlayerSeen]
        for p, s in self.data.items():
            if not s.online:
                if self.should_list(s, bot, _all):
                    to_sort.append(s)
        return sorted(to_sort, key=lambda x: x.target)

    def liver_top(self, bot=False, _all=False):
        to_sort = []        # type: List[PlayerSeen]
        for p, s in self.data.items():
            if s.online:
                if self.should_list(s, bot, _all):
                    to_sort.append(s)
        return sorted(to_sort, key=lambda y: y.target, reverse=True)

    @property
    def lower_data(self) -> Dict[str, PlayerSeen]:
        ret = {}
        for p, s in self.data.items():
            ret[p.lower()] = s
        return ret

    @staticmethod
    def should_list(target: PlayerSeen, bot: bool, _all: bool):
        return bool(bot and target.is_bot) or bool(not bot and not target.is_bot) or _all

    @staticmethod
    def merge(ite: Iterable[PlayerSeen]):
        ret = {}
        for i in ite:
            if i.actual_name not in ret:
                ret[i.actual_name] = i
            else:
                if config.player_prior_in_merge:
                    ret[i.actual_name] = ret[i.actual_name] if i.is_bot else i
                else:
                    ret[i.actual_name] = ret[i.actual_name] if ret[i.actual_name] > i else i
        return sorted(list(ret.copy().values()), key=lambda z: z.target)

    def get(self, name: str) -> Optional[PlayerSeen]:
        return self.lower_data.get(name.lower())

    @new_thread(META.id + '_DataCorrect')
    def correct(self, player_list: List[str]):
        for s in self.data.values():
            if s.online and s.actual_name not in player_list:
                logger.info(f'Corrected player {s.name} status to offline')
                s.leave()

        for p in player_list:
            s = self[p]
            if not s.online:
                logger.info(f'Corrected player {s.name} status to online')
                s.join()

    def __getitem__(self, name: str) -> PlayerSeen:
        if name.lower() not in self.lower_data.keys():
            self[name] = PlayerSeen.deserialize({'name': name})
        return self.lower_data[name.lower()]

    def __setitem__(self, name: str, value: PlayerSeen) -> None:
        self.data[name] = value


storage = SeenStorage().load()
