import os
import json
import time
import datetime


helpmsg = '''------MCD SEEN插件------
命令帮助如下:
!!seen 显示帮助信息
!!seen [玩家] - 查看玩家摸鱼时长
--------------------------------'''


def onPlayerLeave(server, playername):
    t = time.time()
    setSeen(playername, t)


def onPlayerJoin(server, playername):
    setSeen(playername, 'online')


def onServerInfo(server, info):
    if not info.isPlayer:
        return
    
    tokens = info.split()
    command = tokens[0]
    args = tokens[1:]

    if command != '!!seen':
        return

    if args:
        playername = args[0]
        seen(server, info, playername)
    else:
        seenHelp(server, info.player)


def seen(server, info, playername):
    lastSeen = lastSeenTime(playername)
    if lastSeen == "no data":
        msg = "没有 {p} 的数据".format(p=playername)
    elif lastSeen == "online":
        msg = "{p} 没有在摸鱼".format(p=playername)
    else:
        ot = offlineTime(lastSeen)
        msg = "{p} 已经摸了 {t}".format(p=playername, t=ot)

    # server.tell(info.player, msg)
    print(msg)


def offlineTime(lastSeen):
    lastSeen = datetime.datetime.fromtimestamp(lastSeen)
    now = datetime.datetime.now()
    offline = (now - lastSeen).total_seconds()
    return formattedTime(int(offline))
    

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
        values.append(value)

    s = ""
    for i in range(len(values)):
        value = values[i]
        unit = units[i]
        s = "{v} {u} ".format(v=value, u=unit)
    return s


def lastSeenTime(playername):
    seens = seensFromFile()
    playernames = seens.keys()
    if playername in playernames:
        return seens[playername]
    else:
        return "no data"


def seenHelp(server, player):
    server.tell(player, helpmsg)


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
