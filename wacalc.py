#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import random
import requests
import threading
import time
import urllib.parse
from wacalccfg import *
import xml.dom.minidom as xmd

# wacalccfg should contain:
#appids = [
#        "aaaaaa-bbbbbbbbbb",
#...
#        ]


mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']
prefix       = '!'

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=wacalc|descr=Ask Wolfram Alpha to calculate something')

def on_message(client, userdata, message):
    global appids
    global prefix

    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    if topic == 'from/bot/parameter/prefix':
        prefix = text

        return

    if text[0] != prefix:
        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    if channel in channels:
        tokens  = text.split(' ')

        command = tokens[0][1:]

        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'wacalc':
            if len(tokens) >= 2:
                try:
                    query = ' '.join(tokens[1:])

                    appid = random.choice(appids)

                    interpretation = ''
                    response       = ''

                    expr = urllib.parse.quote(query)

                    r    = requests.get(f'http://api.wolframalpha.com/v2/query?appid={appid}&input={expr}')
                    data = r.content.decode('utf8')

                    if data == '':
                        client.publish(response_topic, 'WA returned nothing')

                    dom = xmd.parseString(data)

                    result         = dom.getElementsByTagName('queryresult').item(0)
                    ipod           = result.getElementsByTagName('pod').item(0)
                    rpod           = result.getElementsByTagName('pod').item(1)
                    isubpod        = ipod.getElementsByTagName('subpod').item(0)
                    rsubpod        = rpod.getElementsByTagName('subpod').item(0)
                    interelement   = isubpod.getElementsByTagName('plaintext').item(0)
                    resultelement  = rsubpod.getElementsByTagName('plaintext').item(0)

                    interpretation = f'www.wolframalpha.com interpreted this as: {interelement.firstChild.data}'

                    response       = rpod.getAttribute('title') + ': ' + resultelement.firstChild.data

                    client.publish(response_topic, interpretation)
                    client.publish(response_topic, response)

                except Exception as e:
                    client.publish(response_topic, 'Stephen got confused ({e})')

            else:
                client.publish(response_topic, 'Invalid number of parameters for wacalc')

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
