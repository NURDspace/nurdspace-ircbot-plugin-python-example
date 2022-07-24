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
    client.publish(target_topic, 'cmd=topkarma|descr=Show highest valued word/entity.')
    client.publish(target_topic, 'cmd=toprkarma|descr=Top karma givers.')

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

            command = tokens[0][1:]

            response_topic = f'{topic_prefix}to/irc/{channel}/notice'

            if command == 'karma':
                if len(tokens) != 2:
                    return

                word = tokens[1]

                query = 'SELECT count FROM karma WHERE channel=? AND word=?'

                cur = con.cursor()

                try:
                    cur.execute(query, (channel.lower(), word.lower()))

                    row = cur.fetchone()

                    if row == None:
                        client.publish(response_topic, f'"{word}" has no karma (yet)')

                    else:
                        client.publish(response_topic, f'Karma of "{word}" is {row[0]}')

                except Exception as e:
                    print(f'Exception: {e}')

                cur.close()

            elif command == 'topkarma':
                cur = con.cursor()

                try:
                    cur.execute('SELECT word, count FROM karma WHERE channel=? ORDER BY count DESC LIMIT 5', (channel.lower(),))

                    words = None

                    for row in cur:
                        if words == None:
                            words = ''

                        else:
                            words += ', '

                        words += f'{row[0]} ({row[1]})'

                    if words == None:
                        client.publish(response_topic, 'No karmas')

                    else:
                        client.publish(response_topic, f'Most valued word(s) is/(are): {words}')

                except Exception as e:
                    print(f'Exception: {e}')

                cur.close()

            elif command == 'toprkarma':
                cur = con.cursor()

                try:
                    cur.execute('SELECT who, SUM(count) AS count, COUNT(*) AS n FROM rkarma WHERE channel=? GROUP BY who ORDER BY n DESC LIMIT 5', (channel.lower(),))

                    words = None

                    for row in cur:
                        if words == None:
                            words = ''

                        else:
                            words += ', '

                        person = row[0]

                        if '!' in person:
                            person = person[0:person.find('!')]

                        words += f'{person} ({row[1]} for {row[2]} words)'

                    if words == None:
                        client.publish(response_topic, 'No karmas')

                    else:
                        client.publish(response_topic, f'Top karma givers: {words}')

                except Exception as e:
                    print(f'Exception: {e}')

                cur.close()

            elif command == 'rkarma':
                query = 'SELECT who, count FROM rkarma WHERE channel=? AND word=? ORDER BY who'

                cur = con.cursor()

                try:
                    word = tokens[1]

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
                        client.publish(f'{topic_prefix}to/irc/{channel}/notice', f'"{word}" has no karma (yet)')

                    else:
                        client.publish(f'{topic_prefix}to/irc/{channel}/notice', f'Reverse karma of "{word}": {output}')

                except Exception as e:
                    print(f'Exception: {e}')

                cur.close()

        else:
            if len(text) == 0:
                return

            if text[0] == '(':
                end = text.find(')')

                if end != -1:
                    text = text[1:end - 1]

                    space = text.find(' ', end)

                    if space != -1:
                        text += text[end:space]

                else:
                    return

            else:
                space = text.find(' ')

                if space != -1:
                    text = text[0:space]

            count = 0

            if len(text) >= 2:
                if text[-2:] == '++':
                    count = 1

                elif text[-2:] == '--':
                    count = -1

                text = text[0:-2]

            print('test', text, count, text[-2:0])

            if count != 0:
                print(f'Adding {count} karma to {text}')

                query1 = 'INSERT INTO karma(channel, word, count) VALUES(?, ?, ?) ON CONFLICT(channel, word) DO UPDATE SET count=count+?'

                query2 = 'INSERT INTO rkarma(channel, word, who, count) VALUES(?, ?, ?, ?) ON CONFLICT(channel, word, who) DO UPDATE SET count=count+?'

                try:
                    cur = con.cursor()

                    cur.execute('BEGIN')

                    cur.execute(query1, (channel.lower(), text.lower(), count, count))

                    cur.execute(query2, (channel.lower(), text.lower(), nick.lower(), count, count))

                    cur.execute('COMMIT')

                    cur.execute('SELECT count FROM karma WHERE channel=? AND word=?', (channel.lower(), text.lower()))
                    result = cur.fetchone()

                    cur.close()

                    client.publish(f'{topic_prefix}to/irc/{channel}/notice', f'{text}: {result[0]}')

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
