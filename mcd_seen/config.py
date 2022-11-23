import json

from typing import Union, List
from mcdreforged.api.utils import Serializable
from mcdreforged.api.types import ServerInterface

from mcd_seen.constants import CONFIG_FILE


psi = ServerInterface.get_instance().as_plugin_server_interface()


class Config(Serializable):
    primary_prefix: Union[str, List[str]] = '!!seen'
    primary_rank_prefix: Union[str, List[str]] = '!!seen-top'
    secondary_rank_prefix: Union[str, List[str]] = '!!liver-top'
    seen_top_max: int = 10
    player_prior_in_merge: bool = True
    log_seens: bool = True
    identify_bot: bool = True
    bot_list_delay: float = 0.3
    verbosity: bool
    debug_commands: bool
    debug_prefixes: Union[str, List[str]]

    @staticmethod
    def get_iterable(original: Union[str, List[str]]) -> List[str]:
        if isinstance(original, str):
            return [original]
        return original

    @property
    def seen_prefix(self):
        return self.get_iterable(self.primary_prefix)

    @property
    def seen_top_prefix(self):
        return self.get_iterable(self.primary_rank_prefix)

    @property
    def liver_top_prefix(self):
        return self.get_iterable(self.secondary_rank_prefix)

    @property
    def debug_prefix(self):
        return self.get_iterable(self.serialize().get('debug_prefixes', '!!liver'))

    @property
    def prefixes(self):
        result = []
        for item in [self.seen_prefix, self.seen_top_prefix, self.liver_top_prefix]:
            result += item
        return result

    @property
    def verbose_mode(self):
        return self.serialize().get('verbosity', False)

    @property
    def debug(self):
        return self.serialize().get('debug_commands', False)

    def save(self) -> None:
        with open(CONFIG_FILE, 'w', encoding='UTF-8') as f:
            json.dump(self.serialize(), f, indent=4, ensure_ascii=False)

    @classmethod
    def load(cls) -> 'Config':
        return psi.load_config_simple(
            CONFIG_FILE,
            default_config=cls.get_default().serialize(),
            in_data_folder=False,
            echo_in_console=True,
            target_class=cls
        )


config = Config.load()
