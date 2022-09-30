#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'
# also: pip3 install feedparser or apt install python3-feedparser

import calendar
import feedparser
import paho.mqtt.client as mqtt
import random
import sqlite3
import threading
import time
import urllib.request


import socket
import sys
mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'test', 'nurdsbofh']  # request rss feeds
db_file      = 'rss.db'
prefix       = '!'
announce_in  = ['nurds']  # announcements of new entries

con = sqlite3.connect(db_file)

c = con.cursor()
c.execute('PRAGMA journal_mode=wal')
c.close()

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

cur.execute('SELECT name, url, interval, announce FROM feeds')

for row in cur.fetchall():
    name = row[0]

    feeds[name]              = dict()
    feeds[name]['url']       = row[1]
    feeds[name]['interval']  = row[2]
    feeds[name]['last_poll'] = time.time()
    feeds[name]['tree']      = None
    feeds[name]['announce']  = row[3]

cur.close()

feed_lock = threading.Lock()

def update_feed(client, name):
    global announce_in
    global feed_lock
    global feeds
    global topic_prefix

    now = time.time()

    if now - feeds[name]['last_poll'] < feeds[name]['interval'] and feeds[name]['tree'] != None:
        return

    print(f'Update content for {name} at {time.ctime()} from {feeds[name]["url"]}')

    req = urllib.request.Request(
            feeds[name]['url'], 
            data=None, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                }
            )
    
    fh = urllib.request.urlopen(req)

    tree = feedparser.parse(fh.read())

    output = ''

    for item in tree['items']:
        if 'published_parsed' in item or 'updated_parsed' in item:
            if 'updated_parsed' in item:
                #print(item['updated_parsed'])
                time_diff = calendar.timegm(item['updated_parsed']) - feeds[name]['last_poll']

            else:
                #print(item['published_parsed'])
                time_diff = calendar.timegm(item['published_parsed']) - feeds[name]['last_poll']

            #print(f'Oldness of item for {name}: {time_diff}')

            if time_diff > 0:
                if output != '':
                    output += ' | '

                new_text = f"Feed {name}: {item['title']} {item['link']}"

                if len(output) + len(new_text) > 200:
                    break

                output += new_text

    feed_lock.acquire()

    feeds[name]['tree']       = tree
    feeds[name]['item_index'] = 0
    feeds[name]['last_poll']  = now

    feed_lock.release()

    if output != '' and feeds[name]['announce'] == 1:
        for channel in announce_in:
            response_topic = f'{topic_prefix}to/irc/{channel}/notice'

            client.publish(response_topic, output)

def announce_commands(client):
    global feeds

    target_topic = f'{topic_prefix}to/bot/register'

#    client.publish(target_topic, 'cmd=addrss|descr=Add an RSS feed: addrss <name> <url>')
    client.publish(target_topic, 'cmd=listrss|descr=List RSS feeds')

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

        if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
            response_topic = f'{topic_prefix}to/irc/{channel}/notice'

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

                        feeds[name]              = dict()
                        feeds[name]['url']       = url
                        feeds[name]['interval']  = interval
                        feeds[name]['tree']      = None
                        feeds[name]['last_poll'] = 0

                    except Exception as e:
                        client.publish(response_topic, f'Exception: {e}')

                    cur.close()

                    con.commit()

                else:
                    client.publish(response_topic, 'Name and/or URL missing')

            elif command == 'listrss':
                feed_list = [feed for feed in feeds]

                client.publish(response_topic, f'Available RSS feeds: {", ".join(feed_list)}')

            else:
                name = command.lower()

                if name in feeds:
                    #try:
                    now = time.time()

                    if feeds[name]['tree'] == None or now - feeds[name]['last_poll'] >= feeds[name]['interval']:
                        update_feed(client, name)

                    n_items = len(feeds[name]['tree']['items']) if 'items' in feeds[name]['tree'] else 0

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
                        client.publish(response_topic, f'Feed "{name}" is empty? ({feeds[name]["url"]})')

                    #except Exception as e:
                    #    client.publish(response_topic, f'Error while processing feed "{name}": {e}')

    except Exception as e:
        print(f'Error while processing {message}: {e}')

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

def rss_poller(client):
    while True:
        for name in feeds:
            try:
                update_feed(client, name)

            except Exception as e:
                print(f'Cannot update feed {name}: {e}')

        time.sleep(9)

client = mqtt.Client(f'{socket.gethostname()}_{sys.argv[0]}', clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

t1 = threading.Thread(target=announce_thread, args=(client,))
t1.start()

t2 = threading.Thread(target=rss_poller, args=(client,))
t2.start()

client.loop_forever()
