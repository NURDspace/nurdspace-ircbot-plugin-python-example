#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import json
import paho.mqtt.client as mqtt
import requests
import threading
import time
import urllib.parse

mqtt_server  = 'mqtt.vm.nurd.space'   # TODO: hostname of MQTT server
topic_prefix = 'GHBot/'  # leave this as is
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']  # TODO: channels to respond to
prefix       = '!'  # !command, will be updated by ghbot

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=duckduckgo|descr=Do a duckduckgo query')

def get_json(url):
    r = requests.get(url)

    return r.json()

def get_ddg(query):
    j = get_json(f'http://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json')

    print(j)

    out = ''

    for r in j['RelatedTopics']:
        if out != '':
            out += ', '

        out += f'{r["Text"]}: \2{r["FirstURL"]}\2'

        if len(out) > 350:
            break

    return out

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
    channel = parts[2] if len(parts) >= 3 else 'nurds'  # default channel if can't be deduced
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'  # default nick if it can't be deduced

    if text[0] != prefix:
        return

    command = text[1:].split(' ')[0]

    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'duckduckgo':
            space = text.find(' ')

            if space != -1:
                results = get_ddg(text[space + 1:].strip())

                if results != '':
                    client.publish(response_topic, results)

                else:
                    client.publish(response_topic, 'No results')

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
