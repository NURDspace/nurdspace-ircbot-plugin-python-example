#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import sqlite3
import threading
import time

import socket
import sys

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'test', 'nurdsbofh', 'nurds']

history      = dict()

for channel in channels:
    history[channel] = []

def on_message(client, userdata, message):
    global history

    try:
        text = message.payload.decode('utf-8')

        topic = message.topic[len(topic_prefix):]

        parts   = topic.split('/')
        channel = parts[2] if len(parts) >= 3 else 'nurds'
        nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

        if parts[-1] == 'topic':
            return

        if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
            if len(text) == 0:
                return

            org_in = text

            while True:
                re_idx = text.find('s/')
                if re_idx == -1:
                    break

                sep_1 = text.find('/', re_idx + 2)
                if sep_1 == -1:
                    break

                sep_2 = text.find('/', sep_1 + 2)
                if sep_2 == -1:
                    break

                search_item = text[re_idx + 2:sep_1]

                if len(search_item) == 0:
                    break

                response_topic = f'{topic_prefix}to/irc/{channel}/notice'

                for line in reversed(history[channel]):
                    if search_item in line:
                        new_line = line.replace(search_item, text[sep_1 + 1:sep_2])

                        print(f'old: {org_in}')
                        print(f'new: {new_line}')

                        client.publish(response_topic, f'> {new_line}')

                        break

                # one replacement is good enough for now
                break

            history[channel].append(org_in)

            while len(history[channel]) > 10:
                del history[channel][0]

    except Exception as e:
        print(f'{e}, line number: {e.__traceback__.tb_lineno}')

def on_connect(client, userdata, flags, rc):
    client.subscribe(f'{topic_prefix}from/irc/#')

client = mqtt.Client(f'{socket.gethostname()}_{sys.argv[0]}', clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

client.loop_forever()
