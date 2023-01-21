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
prefix       = '!'
db_file      = 'mqtt.db'

con2 = None

con1 = sqlite3.connect(db_file)

cur = con1.cursor()

try:
    cur.execute('CREATE TABLE mqtt(topic TEXT NOT NULL PRIMARY KEY, value TEXT NOT NULL)')

except sqlite3.OperationalError as oe:
    # should be "table already exists"
    pass

cur.close()

cur = con1.cursor()
cur.execute('PRAGMA journal_mode=wal')
cur.close()

con1.commit()

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

#    client.publish(target_topic, 'cmd=btc|descr=BTC koers')

def cmd_janee(client, response_topic):
    client.publish(response_topic, random.choice(['ja', 'nee', 'ja', 'nein']))

def get_topic(topic):
    cur = con1.cursor()

    cur.execute('SELECT value FROM mqtt WHERE topic=?', (topic,))

    row = cur.fetchone()

    cur.close()

    return row[0]

def on_message(client, userdata, message):
    global choices
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

    if text[0] != prefix:
        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    parts     = text.split(' ')
    command   = parts[0][1:]
    value     = parts[1]  if len(parts) >= 2 else None
    value_all = parts[1:] if len(parts) >= 2 else None

    # print(channel, nick, command, value)

    if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
        command = text[1:].split(' ')[0]

        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

#        if command == 'btc':
#            value = get_topic('vanheusden/bitcoin/bitstamp_usd')

#            client.publish(response_topic, f'btc: {value}')

def on_connect(client, userdata, flags, rc):
    client.subscribe(f'{topic_prefix}from/irc/#')

    client.subscribe(f'{topic_prefix}from/bot/command')

def on_connect_all(client, userdata, flags, rc):
    client.subscribe(f'#')

def on_message_all(client, userdata, message):
    global con2

    text  = message.payload.decode('utf-8')
    topic = message.topic

    if topic_prefix in topic:
        return

    cur = con2.cursor()

    cur.execute('INSERT INTO mqtt(topic, value) VALUES(?, ?) ON CONFLICT(topic) DO UPDATE SET value=?', (topic, text, text))

    cur.close()

    con2.commit()

def announce_thread(client):
    while True:
        try:
            announce_commands(client)

            time.sleep(4.1)

        except Exception as e:
            print(f'Failed to announce: {e}')

def mqtt_all_thread():
    global con2

    client2 = mqtt.Client(sys.argv[0], clean_session=False)
    client2.connect(mqtt_server, port=1883, keepalive=4, bind_address="")
    client2.on_message = on_message_all
    client2.on_connect = on_connect_all

    con2 = sqlite3.connect(db_file)

    while True:
        client2.loop_forever()

client = mqtt.Client(sys.argv[0], clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

t1 = threading.Thread(target=announce_thread, args=(client,))
t1.start()

t2 = threading.Thread(target=mqtt_all_thread, args=())
t2.start()

client.loop_forever()
