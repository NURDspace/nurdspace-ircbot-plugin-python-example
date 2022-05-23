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
db_file      = 'quotes.db'

con = sqlite3.connect(db_file)

cur = con.cursor()
try:
    cur.execute('CREATE TABLE quotes(nr INTEGER PRIMARY KEY, channel TEXT NOT NULL, added_by TEXT NOT NULL, about_whom TEXT NOT NULL, quote TEXT NOT NULL)')
    cur.execute('CREATE INDEX quotes_about_who ON quotes(about_whom)')
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

    client.publish(target_topic, 'cmd=addquote|descr=Add a quote: addquote <nick> <text> -> returns a number')
    client.publish(target_topic, 'cmd=delquote|descr=Delete a quote by the number returned by addquote: delquote <number>')
    client.publish(target_topic, 'cmd=quote|descr=Show a random quote (for a [nick])')
    client.publish(target_topic, 'cmd=re|descr=Show something quoted from you')
    client.publish(target_topic, 'cmd=qs|descr=Search a quote by a search string')

def on_message(client, userdata, message):
    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    # print(topic)

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    parts   = topic.split('/')
    channel = parts[2].lower()
    nick    = parts[3].lower()

    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        tokens  = text.split(' ')

        # print(parts[4], tokens)

        if text[0] == '!' or parts[4] == 'JOIN':
            command = tokens[0][1:]

            # print(command)

            if command == 'addquote':
                # print(tokens)

                if len(tokens) >= 3:
                    cur = con.cursor()

                    try:
                        cur.execute('INSERT INTO quotes(channel, added_by, about_whom, quote) VALUES(?, ?, ?, ?)', (channel, nick, tokens[1].lower(), ' '.join(tokens[2:])))

                        nr = cur.lastrowid

                        client.publish(response_topic, f'Quote about {tokens[1]} stored under number {nr}')

                    except Exception as e:
                        client.publish(response_topic, f'Exception: {e}')

                    cur.close()

                    con.commit()

                else:
                    client.publish(response_topic, 'Nick or quote missing')

            elif command == 'delquote':
                if len(tokens) == 2:
                    cur = con.cursor()

                    nr = tokens[1]

                    try:
                        cur.execute('SELECT COUNT(*) FROM quotes WHERE channel=? AND added_by=? AND nr=?', (channel, nick, nr))

                        row = cur.fetchone()

                        if row[0] >= 1:
                            cur.execute('DELETE FROM quotes WHERE channel=? AND added_by=? AND nr=?', (channel, nick, nr))

                            client.publish(response_topic, f'Quote {nr} deleted')

                        else:
                            client.publish(response_topic, f'No quote exists by the number {nr}')

                    except Exception as e:
                        client.publish(response_topic, f'Exception: {e}')

                    cur.close()

                    con.commit()

                else:
                    client.publish(response_topic, 'Invalid parameters')

            elif command == 're' or parts[4] == 'JOIN' or command == 'quote':
                cur = con.cursor()

                try:
                    if command == 'quote':
                        if len(tokens) == 2:
                            nick = tokens[1]

                        else:
                            nick = None

                    if nick != None and '!' in nick:
                        nick = nick.split('!')[0]

                    if nick == None:
                        cur.execute('SELECT quote, nr, about_whom FROM quotes WHERE channel=? ORDER BY RANDOM() LIMIT 1', (channel,))

                    else:
                        cur.execute('SELECT quote, nr, about_whom FROM quotes WHERE channel=? AND (about_whom=? OR about_whom like ? OR ? like printf("%%%s%%", about_whom)) ORDER BY RANDOM() LIMIT 1', (channel, nick, nick, nick))

                    row = cur.fetchone()

                    if row == None:
                        if command == 're':
                            client.publish(response_topic, f'You have not been quoted yet')

                        elif command == 'quote':
                            client.publish(response_topic, f'No quotes for {nick}')

                    else:
                        client.publish(response_topic, f'[{row[2]}]: {row[0]} ({row[1]})')

                except Exception as e:
                    client.publish(response_topic, f'Exception: {e}')

                cur.close()

            elif command == 'qs':
                cur = con.cursor()

                try:
                    query = ' '.join(tokens[1:])

                    cur.execute('SELECT quote, about_whom, nr FROM quotes WHERE channel=? AND quote like ? ORDER BY RANDOM()', (channel, f'%{query}%'))

                    output = None

                    rows = cur.fetchall()

                    for row in rows:
                        if output == None:
                            output = ''

                        else:
                            output += ' / '

                        output += f'[{row[1]}]: {row[0]} ({row[2]})'

                    if output != None:
                        client.publish(response_topic, f'Matching quote(s): {output}')

                    else:
                        client.publish(response_topic, f'Nothing matched {query}')

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
