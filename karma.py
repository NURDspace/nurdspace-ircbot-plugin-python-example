#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import sqlite3
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'test', 'nurdsbofh', 'nurds']
db_file      = 'karma.db'
prefix       = '!'

con = sqlite3.connect(db_file)

cur = con.cursor()
cur.execute('PRAGMA journal_mode=wal')
cur.close()

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=karma|descr=Show karma of a word/entity.')
    client.publish(target_topic, 'cmd=rkarma|descr=Show reverse karma of a word/entity.')

def on_message(client, userdata, message):
    global prefix

    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        print('Bot restarted?')

        announce_commands(client)

        return

    if topic == 'from/bot/parameter/prefix':
        prefix = text

        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    if channel in channels:
        if text[0] == prefix:
            tokens  = text.split(' ')

            if len(tokens) != 2:
                return

            command = tokens[0][1:]
            word    = tokens[1]

            if command == 'karma':
                query = 'SELECT count FROM karma WHERE channel=? AND word=?'

                cur = con.cursor()

                try:
                    cur.execute(query, (channel.lower(), word.lower()))

                    row = cur.fetchone()

                    if row == None:
                        client.publish(f'{topic_prefix}to/irc/{channel}/privmsg', f'"{word}" has no karma (yet)')

                    else:
                        client.publish(f'{topic_prefix}to/irc/{channel}/privmsg', f'Karma of "{word}" is {row[0]}')

                except Exception as e:
                    print(f'Exception: {e}')

                cur.close()

            elif command == 'rkarma':
                query = 'SELECT who, count FROM rkarma WHERE channel=? AND word=? ORDER BY who'

                cur = con.cursor()

                try:
                    cur.execute(query, (channel.lower(), word.lower()))

                    output = ''

                    for row in cur.fetchall():
                        if output != '':
                            output += ', '

                        who = row[0]

                        if '!' in who:
                            who = who[:who.find('!')]

                        output += f'{who}={row[1]}'

                    if output == '':
                        client.publish(f'{topic_prefix}to/irc/{channel}/privmsg', f'"{word}" has no karma (yet)')

                    else:
                        client.publish(f'{topic_prefix}to/irc/{channel}/privmsg', f'Reverse karma of "{word}": {output}')

                except Exception as e:
                    print(f'Exception: {e}')

                cur.close()

        else:
            for word in text.split(' '):
                count = 0

                add = 0
                while len(word) >= 1 and word[-1] == '+':
                    add += 1

                    word = word[:-1]

                if add >= 2:
                    count += add - 1

                sub = 0
                while len(word) >= 1 and word[-1] == '-':
                    sub += 1

                    word = word[:-1]

                if sub >= 2:
                    count -= sub - 1

                if count != 0:
                    print(f'Adding {count} karma to {word}')

                    query1 = 'INSERT INTO karma(channel, word, count) VALUES(?, ?, ?) ON CONFLICT(channel, word) DO UPDATE SET count=count+?'

                    query2 = 'INSERT INTO rkarma(channel, word, who, count) VALUES(?, ?, ?, ?) ON CONFLICT(channel, word, who) DO UPDATE SET count=count+?'

                    try:
                        cur = con.cursor()

                        cur.execute('BEGIN')

                        cur.execute(query1, (channel.lower(), word.lower(), count, count))

                        cur.execute(query2, (channel.lower(), word.lower(), nick.lower(), count, count))

                        cur.execute('COMMIT')

                        cur.close()

                    except sqlite3.OperationalError as oe:
                        # table does not exist probably

                        try:
                            query = 'CREATE TABLE karma(channel TEXT NOT NULL, word TEXT NOT NULL, count INTEGER, PRIMARY KEY(channel, word))'

                            cur.execute(query)

                            query = 'CREATE TABLE rkarma(channel TEXT NOT NULL, word TEXT NOT NULL, who TEXT NOT NULL, count INTEGER, PRIMARY KEY(channel, word, who))'

                            cur.execute(query)

                            cur.close()

                            con.commit()

                        except Exception as e:
                            print(f'Unexpected exception {e} while handling exception {oe}')

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
