import re

from mcdreforged.api.types import CommandSource, PluginServerInterface
from mcdreforged.api.command import *
from mcdreforged.api.utils import Serializable
from mcdreforged.api.rtext import *
from typing import Callable, Any, List, Union, Optional

from mcd_seen.storage import storage, PlayerSeen
from mcd_seen.constants import *
from mcd_seen.config import config
from mcd_seen.utils import tr, delta_time, formatted_time, bot_name

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
        # Confict check
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
        return '/'.join(ret).strip('/')


def register_command(server: PluginServerInterface):
    def exe(func: Union[Callable[[CommandSource, str], Any], Callable[[CommandSource], Any]], single=False):
        if single:
            return lambda src: func(src)
        return lambda src, ctx: func(src, **ctx)

    # !!seen
    server.register_command(
        Literal(SEEN_PREFIX).on_child_error(CommandError, cmd_error, handled=True).runs(show_help).then(
            QuotableText('player').runs(exe(seen))
        )
    )
    # !!seen-top
    server.register_command(
        Literal(SEEN_TOP_PREFIX).on_child_error(CommandError, cmd_error, handled=True).runs(exe(seen_top, True)).then(
            GreedyText('exarg').runs(exe(seen_top))
        )
    )
    # !!liver
    server.register_command(
        Literal(LIVER_TOP_PREFIX).on_child_error(CommandError, cmd_error, handled=True).runs(exe(liver_top, True)).then(
            QuotableText('exarg').runs(exe(liver_top))
        )
    )
    if DEBUG_MODE:
        server.register_command(
            Literal(DEBUG_PREFIX).requires(lambda src: src.has_permission(4), lambda: 'Permission denied').then(
                Literal('remove').then(
                    GreedyText('players').runs(exe(__remove_player_data))
                )
            )
        )


def show_help(source: CommandSource):
    help_message = tr(
        'help_msg', SEEN_PREFIX, SEEN_TOP_PREFIX, LIVER_TOP_PREFIX, META.name, str(META.version)
    ).strip().splitlines()
    help_msg_rtext = ''
    for line in help_message:
        if help_msg_rtext != '':
            help_msg_rtext += '\n'
        for PREFIX in [SEEN_PREFIX, SEEN_TOP_PREFIX, LIVER_TOP_PREFIX]:
            result = re.search(r'(?<=§7){}[\S ]*?(?=§)'.format(PREFIX), line)
            if result is not None:
                break
        if result is not None:
            cmd = result.group().strip() + ' '
            help_msg_rtext += RText(line).c(RAction.suggest_command, cmd).h(
                tr("hover.help_msg_suggest", cmd.strip()))
        else:
            help_msg_rtext += line
    source.reply(help_msg_rtext)


# Text layout
def top(top_players: List[PlayerSeen], prefix: Union[RTextBase, str]):
    ret, num = RTextList(prefix), 1
    for p in top_players:
        ret.append(f'\n{num}. ', seen_format(p))
        num += 1
    return ret


def seen_format(player: PlayerSeen):
    ret = ''
    # Bot/Player
    ret += '§{}{}§e'.format('5' if player.is_bot else 'd',
                            tr(f'text.{"bot" if player.is_bot else "player"}').capitalize())
    # <player_name>
    ret += f' §e{player.actual_name}§r '
    # has been online/offline for
    ret += tr(f'text.{"bot_liver" if player.is_bot else "player_liver"}') if player.online else tr('text.seen')
    # sec min hrs day
    ret += formatted_time(delta_time(player.target))
    return RText(ret).h(tr('hover.query_player', player.actual_name)).c(
        RAction.run_command, '{} {}'.format(SEEN_PREFIX, player.actual_name)
        )


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
    prefix = tr(f'fmt.seen_top{"_full" if args.full else ""}', config.seen_top_max, args.text)
    if liver:
        prefix = tr('fmt.liver_top', args.text)

    source.reply(top(sorted_list, prefix=prefix))


def liver_top(source: CommandSource, exarg: str = None):
    seen_top(source, exarg, liver=True)


def cmd_error(source: CommandSource):
    source.reply(
        RText(
            tr('mcd_seen.error.cmd_error'), color=RColor.red
        ).c(
            RAction.run_command, SEEN_PREFIX
        ).h(
            tr('mcd_seen.hover.show_help')
        )
    )


def player_data_not_found(source: CommandSource):
    source.reply(
        RText(
            tr('mcd_seen.error.player_data_not_found'), color=RColor.red
        ).c(
            RAction.run_command, SEEN_PREFIX
        ).h(
            tr('mcd_seen.hover.show_help')
        )
    )


# FOR DEBUG ONLY
def __remove_player_data(source: CommandSource, players: str):
    source.get_server()
    player_list = players.split(' ')
    storage.debug_remove(player_list)
