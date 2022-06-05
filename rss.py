#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'
# also: pip3 install feedparser or apt install python3-feedparser

import feedparser
import paho.mqtt.client as mqtt
import random
import sqlite3
import threading
import time
import urllib.request

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'test', 'nurdsbofh']
db_file      = 'rss.db'
prefix       = '!'

con = sqlite3.connect(db_file)

cur = con.cursor()

try:
    cur.execute('CREATE TABLE feeds(name TEXT NOT NULL, url TEXT NOT NULL, interval INTEGER, PRIMARY KEY(name))')

except sqlite3.OperationalError as oe:
    # should be "table already exists"
    pass

cur.close()

cur = con.cursor()
cur.execute('PRAGMA journal_mode=wal')
cur.close()

con.commit()

cur = con.cursor()

feeds = dict()

cur.execute('SELECT name, url, interval FROM feeds')

for row in cur.fetchall():
    name = row[0]

    feeds[name]             = dict()
    feeds[name]['url']      = row[1]
    feeds[name]['interval'] = row[2]
    feeds[name]['last_poll'] = 0
    feeds[name]['tree']     = None

cur.close()

def announce_commands(client):
    global feeds

    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=addrss|descr=Add an RSS feed: addrss <name> <url>')

    for feed in feeds:
        client.publish(target_topic, f'cmd={feed}|descr=Show RSS feed {feed}')

def on_message(client, userdata, message):
    global prefix
    global feeds

    try:
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
        channel = parts[2] if len(parts) >= 3 else 'nurds'
        nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

        if channel in channels:
            response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

            tokens  = text.split(' ')

            if len(tokens[0]) == 0 or tokens[0][0] != prefix:
                return

            command = tokens[0][1:]
            print(command)

            if command == 'addrss':
                if len(tokens) == 3:
                    cur = con.cursor()

                    try:
                        interval = 300
                        name     = tokens[1].lower()
                        url      = tokens[2]

                        cur.execute('INSERT INTO feeds(name, url, interval) VALUES(?, ?, ?)', (name, url, interval))

                        client.publish(response_topic, f'Feed {name} added')

                        feeds[name]             = dict()
                        feeds[name]['url']      = url
                        feeds[name]['interval'] = interval

                    except Exception as e:
                        client.publish(response_topic, f'Exception: {e}')

                    cur.close()

                    con.commit()

                else:
                    client.publish(response_topic, 'Name and/or URL missing')

            else:
                name = command.lower()

                if name in feeds:
                    try:
                        now = time.time()

                        if feeds[name]['tree'] == None or now - feeds[name]['last_poll'] >= feeds[name]['interval']:
                            print(f'Update content for {name}')

                            req = urllib.request.Request(
                                    feeds[name]['url'], 
                                    data=None, 
                                    headers={
                                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                        }
                                    )
                            
                            fh = urllib.request.urlopen(req)

                            feeds[name]['tree']       = feedparser.parse(fh.read())
                            feeds[name]['item_index'] = 0
                            feeds[name]['last_poll']  = now

                        n_items = len(feeds[name]['tree']['items'])

                        if n_items > 0:
                            entry = feeds[name]

                            nr    = entry['item_index']
                            print(f'entry {nr} out of {n_items}')

                            text  = f"Feed {name}: {entry['tree']['items'][nr]['title']} {entry['tree']['items'][nr]['link']}"

                            nr += 1
                            if nr >= n_items:
                                nr = 0

                            feeds[name]['item_index'] = nr

                            client.publish(response_topic, text)

                        else:
                            client.publish(response_topic, f'Feed "{name}" is empty?')

                    except Exception as e:
                        client.publish(response_topic, f'Error while processing feed "{name}": {e}')

    except Exception as e:
        print(f'Error while processing {message}: {e}')

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
