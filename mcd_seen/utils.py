import os.path
import re
import time
from typing import Optional, Union

from mcdreforged.api.rtext import *
from mcdreforged.api.types import MCDReforgedLogger, ServerInterface

from mcd_seen.config import config
from mcd_seen.constants import LOG_FILE, NEW_LOG_PATH, OLD_LOG_FILE

TextType = Union[str, RText]
psi = ServerInterface.get_instance().as_plugin_server_interface()


class SeenLogger(MCDReforgedLogger):
    __global_instance = None    # type: Optional[SeenLogger]
    __debug = False

    def debug(self, *args, **kwargs):
        if self.__debug:
            super(MCDReforgedLogger, self).debug(*args, **kwargs)

    @classmethod
    def set_verbosity(cls):
        cls.__debug = config.verbose_mode

    @classmethod
    def get_instance(cls) -> MCDReforgedLogger:
        if cls.__global_instance is None:
            cls.set_verbosity()
            cls.__global_instance = cls(plugin_id=psi.get_self_metadata().id)
            old_converted = False
            try:
                if os.path.isfile(OLD_LOG_FILE):
                    os.rename(OLD_LOG_FILE, NEW_LOG_PATH)
                    old_converted = True
            except Exception as exc:
                cls.__global_instance.warning(f'Move old logs to new place failed: {str(exc)}')
            cls.__global_instance.set_file(LOG_FILE)
            if old_converted:
                cls.__global_instance.info('Moved old log file to new place')
        return cls.__global_instance


logger = SeenLogger.get_instance()


def log_seen(msg: str, *args, **kwargs):
    if config.log_seens:
        logger.info(msg, *args, **kwargs)


def rclick(msg: str, hover: str, cmd: str, action: RAction = RAction.run_command,
           color: Optional[RColor] = None, style: Optional[RStyle] = None) -> RText:
    return RText(msg, color, style).h(hover).c(action, cmd)


def verify_player_name(name: str) -> bool:
    return re.fullmatch(r'\w+', name) is not None


def ntr(translation_key: str, *args, _mcdr_tr_language: Optional[str] = None, language: Optional[str] = None,
        allow_failure: bool = True, **kwargs) -> TextType:
    """
    Directly translate your keys to text
    :param translation_key: Your translation key
    :param args: Format args
    :param language: Required language specified, deprecated in MCDReforged v2.12, migrate to _mcdr_tr_language
    :param _mcdr_tr_language: Required language specified
    :param allow_failure: Allow failure to be thrown
    :param kwargs: Format kwargs
    :return: Your message text that can be processed by MCDReforged
    """
    if _mcdr_tr_language is None:
        _mcdr_tr_language = language
    try:
        return psi.tr(
            translation_key, *args, _mcdr_tr_language=_mcdr_tr_language, allow_failure=False, **kwargs
        )
    except (KeyError, ValueError):
        fallback_language = psi.get_mcdr_language()
        try:
            if fallback_language == 'en_us':
                raise KeyError(translation_key)
            return psi.tr(
                translation_key, *args, _mcdr_tr_language='en_us', allow_failure=allow_failure, **kwargs
            )
        except (KeyError, ValueError):
            languages = []
            for item in (_mcdr_tr_language, fallback_language, 'en_us'):
                if item not in languages:
                    languages.append(item)
            languages = ', '.join(languages)
            if allow_failure:
                logger.error(f'Error translate text "{translation_key}" to language {languages}')
            else:
                raise KeyError(f'Translation key "{translation_key}" not found with language {languages}')


def tr(translation_key: str, *args, with_prefix=True, **kwargs) -> RTextMCDRTranslation:
    """
    Return a translation object
    :param translation_key: Your translation key
    :param args: Format args
    :param with_prefix: Auto fill translation key prefix
    :param kwargs: Format kwargs
    :return: Your message text that can be processed by MCDReforged
    """
    plugin_id = psi.get_self_metadata().id
    if with_prefix and not translation_key.startswith(plugin_id):
        translation_key = f"{plugin_id}.{translation_key}"
    return psi.rtr(translation_key, *args, **kwargs).set_translator(ntr)


def htr(translation_key: str, *args, **kwargs) -> RTextMCDRTranslation:
    """
    Magic(xD)! Translate your help message to an advanced rich text
    :param translation_key: Your translation key
    :param args: Format args
    :param kwargs: Format kwargs
    :return: Your message text that can be processed by MCDReforged
    """

    def __get_regex_result(line: str) -> Optional["re.Match"]:
        suggest_pattern = r'(?<=§7){}[\S ]*?(?=§)'
        for prefix in config.prefixes:
            result = re.search(suggest_pattern.format(prefix), line)
            if result is not None:
                return result
        return None

    def __htr(key: str, *inner_args, language: Optional[str] = None, **inner_kwargs):
        original, processed = ntr(key, *inner_args, language=language, **inner_kwargs), []
        if not isinstance(original, str):
            return key
        for line in original.splitlines():
            result = __get_regex_result(line)
            action = RAction.suggest_command
            hover = "hover.help_msg_suggest"
            if result is not None:
                command = result.group() + ' '
                processed.append(RText(line).c(action, command).h(tr(hover, command)))
            else:
                processed.append(line)
        return RTextBase.join('\n', processed)

    return tr(translation_key, *args, **kwargs).set_translator(__htr)


def fmt_time_tr(translation_key: str, t: Union[int, str], _mcdr_tr_language: Optional[str] = None, language: Optional[str] = None,
                allow_failure: bool = True) -> str:
    if _mcdr_tr_language is None:
        _mcdr_tr_language = language
    t = int(t)
    values = []
    units = ntr(translation_key, language=_mcdr_tr_language, allow_failure=allow_failure).split(' ')
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

    s = []
    for i in range(len(values)):
        value = values[i]
        unit = units[i]
        s.append("{v} {u}".format(v=value, u=unit))
    s.reverse()
    return '§6' + ' '.join(s) + '§r'


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
