#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import random
import sqlite3
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET

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
    feeds[row[0]]             = dict()
    feeds[row[0]]['url']      = row[1]
    feeds[row[0]]['interval'] = row[2]
    feeds[row[0]]['last_poll'] = 0
    feeds[row[0]]['text']     = None

cur.close()

def announce_commands(client):
    global feeds

    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=addrss|descr=Add an RSS feed: addrss <name> <url>')

    for feed in feeds:
        client.publish(target_topic, f'cmd={feed}|descr=Show RSS feed {feeds[feed]}')

def on_message(client, userdata, message):
    global prefix
    global feeds

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

        if tokens[0][0] != prefix:
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
                # TODO show latest, not random

                try:
                    now = time.time()

                    if feeds[name]['text'] == None or now - feeds[name]['last_poll'] >= feeds[name]['interval']:
                        print(f'Update content for {name}')

                        req = urllib.request.Request(
                                feeds[name]['url'], 
                                data=None, 
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                    }
                                )
                        
                        fh = urllib.request.urlopen(req)

                        feeds[name]['text']      = fh.read()
                        feeds[name]['last_poll'] = now

                    tree = ET.ElementTree(ET.fromstring(feeds[name]['text']))

                    root = tree.getroot()

                    ch = root.find('channel')

                    titles = []

                    for item in ch.findall('item'):
                        title = item.find('title')
                        titles.append(title.text)

                    txt = random.choice(titles)

                    client.publish(response_topic, f'Feed {name}: {txt}')

                except Exception as e:
                    client.publish(response_topic, f'Error while processing feed {name}: {e}')

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
