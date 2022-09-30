#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

# CREATE TABLE messages(nr INTEGER PRIMARY KEY, ts DATETIME DEFAULT CURRENT_TIMESTAMP, for_whom text not null, by_whom text not null, what text not null);
# CREATE INDEX for_whom_idx ON messages(for_whom);

import paho.mqtt.client as mqtt
import sqlite3
import threading
import time

import socket
import sys

mqtt_server  = 'mqtt.vm.nurd.space'   # TODO: hostname of MQTT server
topic_prefix = 'GHBot/'  # leave this as is
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']  # TODO: channels to respond to
prefix       = '!'  # !command, will be updated by ghbot
db           = 'message.db'

con = sqlite3.connect(db)

cur = con.cursor()
cur.execute('PRAGMA journal_mode=wal')
cur.close()

con.commit()


def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=message|descr=Leave a message')

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

    if len(text) == 0:
        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'  # default channel if can't be deduced
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'  # default nick if it can't be deduced

    if len(parts) >= 4 and parts[3] == 'topic':
        return

    command = text[1:].split()[0]

    if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        # check for stored messages for this nick
        try:
            if '!' in nick:
                nick = nick[0:nick.find('!')]

            nick = nick.lower()

            nick_topic = f'{topic_prefix}to/irc-person/{nick}'

            print(f'Check for messages for {nick}')

            q = 'SELECT nr, ts, by_whom, what FROM messages WHERE for_whom=?'

            cur = con.cursor()

            cur.execute(q, (nick, ))

            for row in cur.fetchall():
                nr      = row[0]
                by_whom = row[2]
                ts      = row[1]
                what    = row[3]

                print(f'Sending message by {by_whom} to {nick}')

                client.publish(nick_topic, f'{by_whom}@{ts}: {what}')

                if '!' in by_whom:
                    by_whom = by_whom[0:by_whom.find('!')]

                by_whom_topic = f'{topic_prefix}to/irc-person/{by_whom}'

                client.publish(by_whom_topic, f'Message for {nick} from {ts} delivered ({what})')

                cur2 = con.cursor()
                cur2.execute('DELETE FROM messages WHERE nr=?', (nr,))
                cur2.close()

            cur.close()

            con.commit()

        except Exception as e:
            print(f'exception: {e}, line number: {e.__traceback__.tb_lineno}')

        # process any command

        if command == 'message':
            try:
                tokens = text.split()

                if len(tokens) < 3:
                    return

                user   = tokens[1].lower()

                cur = con.cursor()
                cur.execute('INSERT INTO messages(by_whom, for_whom, what) VALUES(?, ?, ?)', (nick, user, text,))
                cur.close()

                con.commit()

                client.publish(response_topic, f'Message for {user} stored')

            except Exception as e:
                client.publish(response_topic, f'Message for {user} NOT stored: {e}, line number: {e.__traceback__.tb_lineno}')

def on_connect(client, userdata, flags, rc):
    client.subscribe(f'{topic_prefix}from/irc/#')

    client.subscribe(f'{topic_prefix}from/bot/command')

def announce_thread(client):
    while True:
        try:
            announce_commands(client)

            time.sleep(4.1)

        except Exception as e:
            print(f'Failed to announce: {e}')

client = mqtt.Client(f'{socket.gethostname()}_{sys.argv[0]}', clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

t = threading.Thread(target=announce_thread, args=(client,))
t.start()

client.loop_forever()
