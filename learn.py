#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import sqlite3
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'test', 'nurdsbofh']
db_file      = 'learn.db'
prefix       = '!'

con = sqlite3.connect(db_file)

cur = con.cursor()
try:
    cur.execute('CREATE TABLE learn(nr INTEGER PRIMARY KEY, channel TEXT NOT NULL, added_by TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL)')
    cur.execute('CREATE INDEX learn_key ON learn(key)')
except sqlite3.OperationalError as oe:
    # should be "table already exists"
    pass
cur.close()

cur = con.cursor()
cur.execute('PRAGMA journal_mode=wal')
cur.close()

con.commit()

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=learn|descr=Store a fact about something')
    client.publish(target_topic, 'cmd=dellearn|descr=Forget a fact')

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

    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        tokens  = text.split(' ')

        command = tokens[0][1:]

        if command == 'learn' and tokens[0][0] == prefix:
            # print(tokens)

            if len(tokens) >= 4 or tokens[2].lower() != 'is':
                # !learn bla is something
                # 0      1   2  3

                cur = con.cursor()

                try:
                    cur.execute('INSERT INTO learn(channel, added_by, key, value) VALUES(?, ?, ?, ?)', (channel, nick, tokens[1].lower(), ' '.join(tokens[3:])))

                    nr = cur.lastrowid

                    client.publish(response_topic, f'Fact about {tokens[1]} stored under number {nr}')

                except Exception as e:
                    client.publish(response_topic, f'Exception: {e}')

                cur.close()

                con.commit()

            else:
                client.publish(response_topic, 'Nick or fact missing. Also the word "is" should be there.')

        elif command == 'dellearn' and tokens[0][0] == prefix:
            if len(tokens) == 2:
                cur = con.cursor()

                try:
                    nr = tokens[1]

                    cur.execute('DELETE FROM learn WHERE channel=? AND nr=?', (channel, nr))

                    client.publish(response_topic, f'Fact {nr} deleted')

                except Exception as e:
                    client.publish(response_topic, f'Exception: {e}')

                cur.close()

                con.commit()

            else:
                client.publish(response_topic, 'Invalid number of parameters: parameter should be the fact-number')

        elif len(command) > 1 and command[-1] == '?':
            cur = con.cursor()

            try:
                verbose = True if len(tokens) == 2 and tokens[1] == '-v' else False

                word = tokens[0][0:-1]

                cur.execute('SELECT value, nr FROM learn WHERE channel=? AND key=? ORDER BY value', (channel, word.lower()))

                facts = None

                for row in cur.fetchall():
                    item = f'{row[0]} ({row[1]})' if verbose else row[0]

                    if facts == None:
                        facts = item

                    else:
                        facts += ' / ' + item

                if facts != None:
                    client.publish(response_topic, f'{word} is: {facts}')

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
