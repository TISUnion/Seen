# -*- coding: utf-8 -*-
import copy
import os
import json
import time


helpmsg = '''------MCD SEEN插件------
命令帮助如下:
!!seen 显示帮助信息
!!seen [玩家] - 查看玩家摸鱼时长
!!seen-top 查看摸鱼榜
!!liver 查看所有在线玩家爆肝时长
--------------------------------'''


def tell(server, player, message):
    for line in message.splitlines():
        if line.startswith(u'/tellraw'.encode('utf-8')):
            line = line.replace('{player}', player)
            line = line.encode('utf-8')
            server.execute(line)
        else:
            if isinstance(line, unicode):
                line = line.encode('utf-8')
            server.tell(player, line)


def onPlayerLeave(server, playername):
    t = now_time()
    set_seen(playername, t, 'left')


def onPlayerJoin(server, playername):
    t = now_time()
    set_seen(playername, t, 'joined')


def onServerInfo(server, info):
    if not info.isPlayer:
        return

    tokens = info.content.split()
    command = tokens[0]
    args = tokens[1:]

    # try:
    if command == '!!seen':
        if args:
            playername = args[0]
            seen(server, info, playername)
        else:
            seen_help(server, info.player)
    elif command == '!!liver':
        liver(server, info)
    elif command == '!!seen-top':
        seen_top(server, info)

    # except:
    #     f = traceback.format_exc()
    #     tell(server, info.player, f)


# MCDR compatibility

def on_load(server, old):
    server.add_help_message('!!seen', '查看摸鱼榜/爆肝榜帮助')


def on_player_joined(server, player):
    onPlayerJoin(server, player)


def on_player_left(server, player):
    onPlayerLeave(server, player)


def on_info(server, info):
    info2 = copy.deepcopy(info)
    info2.isPlayer = info2.is_player
    onServerInfo(server, info2)


def seen(server, info, playername):
    joined, left = player_seen(playername)
    if (left and joined) == 0:
        msg = "没有 §e{p}§r 的数据".format(p=playername)
    elif left < joined:
        dt = delta_time(joined)
        ft = formatted_time(dt)
        msg = "§e{p}§r 没有在摸鱼, 已经肝了 §a{t}".format(p=playername, t=ft)
    elif left >= joined:
        dt = delta_time(left)
        ft = formatted_time(dt)
        msg = "§e{p}§r 已经摸了 §6{t}".format(p=playername, t=ft)

    server.tell(info.player, msg)


def liver(server, info):
    seens = seens_from_file()
    players = seens.keys()

    result = []
    for player in players:
        joined, left = player_seen(player)
        if left < joined:
            result.append([joined, player])
    result.sort()
    for r in result:
        joined, player = r
        dt = delta_time(joined)
        ft = formatted_time(dt)
        msg = "§e{p}§r 已经肝了 §a{t}".format(p=player, t=ft)
        server.tell(info.player, msg)


def seen_top(server, info):
    seens = seens_from_file()
    players = seens.keys()

    result = []
    for player in players:
        joined, left = player_seen(player)
        if left > joined:
            result.append([left, player])
    result.sort()
    top_num = min(len(result), 10)
    for i in range(top_num):
        r = result[i]
        left, player = r
        dt = delta_time(left)
        ft = formatted_time(dt)
        msg = "{i}. §e{p}§r 已经摸了 §6{t}".format(i=i+1, p=player, t=ft)
        server.tell(info.player, msg)


def now_time():
    t = time.time()
    return int(t)


def delta_time(last_seen):
    now = now_time()
    return now - abs(last_seen)


def formatted_time(t):
    t = int(t)
    values = []
    units = ["秒", "分", "小时", "天"]
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
    return s


def player_seen(playername):
    seens = seens_from_file()
    seen = seens.get(playername, 0)
    if seen:
        joined = seen.get('joined', 0)
        left = seen.get('left', 0)
        return joined, left
    else:
        return 0, 0


def seen_help(server, player):
    for line in helpmsg.splitlines():
        server.tell(player, line)


def set_seen(playername, time, type):
    seens = seens_from_file()
    player = seens.get(playername)
    if not player:
        seens[playername] = {
            'joined': 0,
            'left': 0,
        }
    seens[playername][type] = time

    save_seens(seens)


def init_file():
    with open("seen.json", "w") as f:
        d = {}
        s = json.dumps(d)
        f.write(s)


def seens_from_file():
    if not os.path.exists("seen.json"):
        init_file()
    with open("seen.json", "r") as f:
        seens = json.load(f)
    return seens


def save_seens(seens):
    with open("seen.json", "w") as f:
        json_seens = json.dumps(seens)
        f.write(json_seens)
