#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import sqlite3
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']
db_file      = 'seen.db'
prefix       = '!'

con = sqlite3.connect(db_file)

cur = con.cursor()

cur.execute('PRAGMA strict=ON')

try:
    cur.execute('CREATE TABLE seen(channel TEXT NOT NULL, who TEXT NOT NULL, ts TEXT NOT NULL, quote TEXT NOT NULL, PRIMARY KEY(channel, who))')

except sqlite3.OperationalError as oe:
    print(oe)
    # should be "table already exists"
    pass

cur.close()

cur = con.cursor()
cur.execute('PRAGMA journal_mode=wal')
cur.close()

con.commit()

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=seen|descr=When did we saw last that loser?')

def on_message(client, userdata, message):
    global prefix

    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    if topic == 'from/bot/parameter/prefix':
        prefix = text

        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    # store
    cur = con.cursor()

    try:
        now = int(time.time())

        mod_nick = nick

        if '!' in mod_nick:
            mod_nick = mod_nick[0:mod_nick.find('!')]

        cur.execute("INSERT INTO seen(channel, who, ts, quote) VALUES(?, ?, strftime('%Y-%m-%d %H:%M:%S','now'), ?) ON CONFLICT(channel, who) DO UPDATE SET ts=strftime('%Y-%m-%d %H:%M:%S','now'), quote=?", (channel, mod_nick.lower(), text, text))

    except Exception as e:
        print(e)

    cur.close()

    con.commit()

    # commands
    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        tokens  = text.split(' ')

        command = tokens[0][1:]

        if command == 'seen' and tokens[0][0] == prefix and len(tokens) == 2:
            nick = tokens[1].lower()
 
            cur = con.cursor()

            try:
                word = tokens[0][0:-1]

                cur.execute('SELECT ts AS "[timestamp]", quote FROM seen WHERE channel=? AND who=?', (channel, nick))

                row = cur.fetchone()

                if row == None:
                    client.publish(response_topic, f'Never saw {nick}')

                else:
                    client.publish(response_topic, f'Last time we saw {nick} was on {row[0]} saying "{row[1]}"')

            except Exception as e:
                client.publish(response_topic, f'Exception: {e}')

            cur.close()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f'{topic_prefix}from/irc/#')

        client.subscribe(f'{topic_prefix}from/bot/command')

def announce_thread(client):
    while True:
        try:
            announce_commands(client)

            time.sleep(4.1)

        except Exception as e:
            print(f'Failed to announce: {e}')

client = mqtt.Client()
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")
client.on_message = on_message
client.on_connect = on_connect

t = threading.Thread(target=announce_thread, args=(client,))
t.start()

client.loop_forever()
