#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import datetime
import json
import paho.mqtt.client as mqtt
import requests
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']
prefix       = '!'

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=events|descr=NURDspace events')

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
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    if text[0] != prefix:
        return

    command = text[1:].split(' ')[0]

    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'events':
            now = datetime.datetime.now()

            from_day   = now.strftime("%d")
            from_month = now.strftime("%m")
            from_year  = now.strftime("%Y")

            url = f'https://nurdspace.nl/Special:Ask/-5B-5BCategory:Events-5D-5D-20-5B-5BDate::-3E-20{from_month}-20{from_day}-20{from_year}-5D-5D-20OR-20-5B-5BDateEnd::-3E-20{from_month}-20{from_day}-20{from_year}-5D-5D/-3FName/-3FDate/-3FDateEnd/-3FLocation/-3F-23-2D/format%3Djson/limit%3D5/offset%3D0/sort%3DDate/mainlabel%3D-2D/default%3DNone-20currently-20planned'

            r = requests.get(url, timeout=10)

            events_j = json.loads(r.content.decode('ascii'))

            events = []

            for e in events_j['results']:
                event = events_j['results'][e]

                events.append(f'{e}: {event["fullurl"]}')

            client.publish(response_topic, ', '.join(events))

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
