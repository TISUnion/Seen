# -*- coding: utf-8 -*-


import os
import json
import time


helpmsg = '''------MCD SEEN插件------
命令帮助如下:
!!seen 显示帮助信息
!!seen [玩家] - 查看玩家摸鱼时长
--------------------------------'''


def onPlayerLeave(server, playername):
    t = nowTime()
    setSeen(playername, t)


def onPlayerJoin(server, playername):
    t = -nowTime()
    setSeen(playername, t)


def onServerInfo(server, info):
    if not info.isPlayer:
        return
    
    tokens = info.content.split()
    command = tokens[0]
    args = tokens[1:]

    if command == '!!seen':
        if args:
            playername = args[0]
            seen(server, info, playername)
        else:
            seenHelp(server, info.player)


def seen(server, info, playername):
    lastSeen = lastSeenTime(playername)
    if lastSeen == "no data":
        msg = "没有 §e{p}§r 的数据".format(p=playername)
    elif lastSeen < 0:
        ot = onlineTime(lastSeen)
        ft = formattedTime(ot)
        msg = "§e{p}§r 没有在摸鱼, 已经肝了 §6{t}".format(p=playername, t=ft)
    elif lastSeen >= 0:
        ot = offlineTime(lastSeen)
        ft = formattedTime(ot)
        msg = "§e{p}§r 已经摸了 §6{t}".format(p=playername, t=ft)

    server.tell(info.player, msg)


def nowTime():
    t = time.time()
    return int(t)


def offlineTime(lastSeen):
    now = nowTime()
    return now - lastSeen


def onlineTime(lastSeen):
    now = nowTime()
    return now - (-lastSeen)


def formattedTime(t):
    values = []
    units = ["秒", "分钟", "小时", "天"]
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


def lastSeenTime(playername):
    seens = seensFromFile()
    playernames = seens.keys()
    if playername in playernames:
        return seens[playername]
    else:
        return "no data"


def seenHelp(server, player):
    for line in helpmsg.splitlines():
        server.tell(player, line)


def setSeen(playername, seen):
    seens = seensFromFile()
    seens[playername] = seen
    saveSeens(seens)


def initFile():
    with open("seen.json", "w") as f:
        d = {}
        s = json.dumps(d)
        f.write(s)


def seensFromFile():
    if not os.path.exists("seen.json"):
        initFile()
    with open("seen.json", "r") as f:
        seens = json.load(f)
    return seens


def saveSeens(seens):
    with open("seen.json", "w") as f:
        jsonSeens = json.dumps(seens)
        f.write(jsonSeens)
