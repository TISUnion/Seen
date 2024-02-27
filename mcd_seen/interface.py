from typing import Callable, Any, List, Union, Optional

from mcdreforged.api.command import *
from mcdreforged.api.rtext import *
from mcdreforged.api.types import CommandSource, PluginServerInterface
from mcdreforged.api.utils import Serializable

from mcd_seen.config import config
from mcd_seen.storage import storage, PlayerSeen
from mcd_seen.utils import tr, delta_time, bot_name, psi, ntr, htr, fmt_time_tr

TOP_OPTIONS = {
        '-bot': 'bot',
        '-all': 'all',
        '-merge': 'merge',
        '-full': 'full'
    }


class ExtraArguments(Serializable):
    bot: bool = False
    all: bool = False
    merge: bool = False
    full: bool = False

    @classmethod
    def parse(cls, arg_string: Optional[str], liver: bool = False):
        if not isinstance(arg_string, str):
            return cls.get_default()
        data = cls.serialize(cls.get_default())
        args = arg_string.split(' ')
        for arg, mode in TOP_OPTIONS.items():
            if arg in args:
                data[mode] = True
                args.remove(arg)
        data = cls.deserialize(data)
        # Conflict check
        if [data.all, data.merge, data.bot].count(True) > 1 or (data.full and liver) or (len(args) != 0):
            raise IllegalArgument(f'Illegal argument: {arg_string}', 1)
        if liver and not data.get_all:
            data.all = True
        return data

    @property
    def get_all(self):
        return self.all or self.merge

    @property
    def text(self):
        ret = []
        for o, value in self.serialize().items():
            if value and not o == 'full':
                ret.append(tr(f'text.top_{o}'))
        if len(ret) == 0:
            ret.append(tr('text.top_normal'))
        return RTextBase.join('/', ret)


def reload_self(source: CommandSource):
    psi.reload_plugin(psi.get_self_metadata().id)
    source.reply(tr('text.reloaded'))


def register_command(server: PluginServerInterface):
    def exe(func: Union[Callable[[CommandSource, str], Any], Callable[[CommandSource], Any]], single=False):
        if single:
            return lambda src: func(src)
        return lambda src, ctx: func(src, **ctx)

    # !!seen
    server.register_command(
        Literal(config.seen_prefix).on_child_error(
            CommandError, cmd_error, handled=True).runs(show_help).then(
            Literal('reload').runs(reload_self)
        ).then(
            QuotableText('player').runs(exe(seen))
        )
    )
    # !!seen-top
    server.register_command(
        Literal(config.seen_top_prefix).on_child_error(
            CommandError, cmd_error, handled=True).runs(exe(seen_top, True)).then(
            GreedyText('exarg').runs(exe(seen_top))
        )
    )
    # !!liver
    server.register_command(
        Literal(config.liver_top_prefix).on_child_error(
            CommandError, cmd_error, handled=True).runs(exe(liver_top, True)).then(
            QuotableText('exarg').runs(exe(liver_top))
        )
    )
    if config.debug:
        server.register_command(
            Literal(config.debug_prefix).requires(
                lambda src: src.has_permission(4), lambda: 'Permission denied').then(
                Literal('remove').then(
                    GreedyText('players').runs(exe(__remove_player_data))
                )
            )
        )


def show_help(source: CommandSource):
    meta = psi.get_self_metadata()
    msg = htr(
        'help_msg',
        config.seen_prefix[0],
        config.seen_top_prefix[0],
        config.liver_top_prefix[0],
        meta.name,
        str(meta.version)
    )
    source.reply(msg)


# Text layout
def top(top_players: List[PlayerSeen], prefix: Union[RTextBase, str]):
    ret, num = [prefix], 1
    for p in top_players:
        ret.append(RTextList(f'{num}. ', seen_format(p)))
        num += 1
    return RTextBase.join('\n', ret)


def seen_format(player: PlayerSeen):
    return tr('text', player=player).set_translator(seen_fmt_tr)


def seen_fmt_tr(translation_key: str, player: PlayerSeen, _mcdr_tr_language: Optional[str] = None, language: Optional[str] = None, allow_failure: bool = True):
    if _mcdr_tr_language is None:
        _mcdr_tr_language = language

    def ttr(key: str, *args, **kwargs):
        return ntr(f'{translation_key}.{key}', *args, language=_mcdr_tr_language, allow_failure=allow_failure, **kwargs)
    ret = []
    # Bot/Player
    color = '§5' if player.is_bot else '§d'
    ret.append(f"{color}{ttr('bot' if player.is_bot else 'player').capitalize()}§r")
    # <player_name>
    ret.append(f'§e{player.actual_name}§r')
    # has been online/offline for
    ret.append(ttr('bot_liver' if player.is_bot else 'player_liver') if player.online else ttr('seen'))
    # sec min hrs day
    ret.append(fmt_time_tr(
        'mcd_seen.fmt.time_seen', t=delta_time(player.target), _mcdr_tr_language=_mcdr_tr_language, allow_failure=allow_failure))

    ret = ' '.join(ret)
    ret = RText(ret).h(tr('hover.query_player', player.actual_name)).c(
        RAction.run_command, '{} {}'.format(config.seen_prefix[0], player.actual_name)
        )
    return ret


def seen(source: CommandSource, player: str):
    to_display = []
    player_seen, bot_seen = storage.get(player), storage.get(bot_name(player))
    if player_seen is not None:
        to_display.append(seen_format(player_seen))
    if bot_seen is not None:
        to_display.append(seen_format(bot_seen))
    if len(to_display) == 0:
        player_data_not_found(source)
    source.reply(RText.join('\n', to_display))


def seen_top(source: CommandSource, exarg: str = None, liver: bool = False):
    # parse arguments
    args = ExtraArguments.parse(exarg, liver)
    # get list
    if liver:
        sorted_list = storage.liver_top(bot=args.bot, _all=args.get_all)
    else:
        sorted_list = storage.seen_top(bot=args.bot, _all=args.get_all)
    # -merge
    sorted_list = storage.merge(sorted_list) if args.merge else sorted_list
    # -full
    sorted_list = sorted_list if args.full else sorted_list[:config.seen_top_max]
    # get prefix
    prefix = tr(f'fmt.seen_top{"_full" if args.full else ""}', num=config.seen_top_max, arg=args.text)
    if liver:
        prefix = tr('fmt.liver_top', arg=args.text)

    source.reply(top(sorted_list, prefix=prefix))


def liver_top(source: CommandSource, exarg: str = None):
    seen_top(source, exarg, liver=True)


def cmd_error(source: CommandSource):
    source.reply(
        tr('mcd_seen.error.cmd_error').set_color(color=RColor.red).c(
            RAction.run_command, config.seen_prefix[0]
        ).h(
            tr('mcd_seen.hover.show_help')
        )
    )


def player_data_not_found(source: CommandSource):
    source.reply(
        tr('mcd_seen.error.player_data_not_found').set_color(color=RColor.red).c(
            RAction.run_command, config.seen_prefix[0]
        ).h(
            tr('mcd_seen.hover.show_help')
        )
    )


# FOR DEBUG ONLY
def __remove_player_data(source: CommandSource, players: str):
    source.get_server()
    player_list = players.split(' ')
    storage.debug_remove(player_list)
