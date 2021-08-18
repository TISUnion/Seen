import json

from mcd_seen.constants import CONFIG_FILE

from mcdreforged.api.utils import Serializable
from mcdreforged.api.types import ServerInterface


class Config(Serializable):
    seen_top_max: int = 10
    player_prior_in_merge: bool = True
    log_seens: bool = True
    identify_bot: bool = True
    bot_list_delay: float = 0.3

    def save(self) -> None:
        with open(CONFIG_FILE, 'w', encoding='UTF-8') as f:
            json.dump(self.serialize(), f, indent=4, ensure_ascii=False)

    @classmethod
    def load(cls) -> 'Config':
        return ServerInterface.get_instance().as_plugin_server_interface().load_config_simple(
            CONFIG_FILE, default_config=cls.get_default().serialize(), in_data_folder=False, echo_in_console=True,
            target_class=cls
        )


config = Config.load()
