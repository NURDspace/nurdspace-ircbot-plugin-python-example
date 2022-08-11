#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import datetime
import json
import math
import paho.mqtt.client as mqtt
import pytz
import requests
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'   # TODO: hostname of MQTT server
topic_prefix = 'GHBot/'  # leave this as is
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']  # TODO: channels to respond to
prefix       = '!'  # !command, will be updated by ghbot

netherlands_tz = pytz.timezone("Europe/Amsterdam")

prev_j = None

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=nlenergie|descr=Stroomgebruik in Nederland op dit moment')

def on_message(client, userdata, message):
    global prefix
    global prev_j

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
        response_topic = f'{topic_prefix}to/irc/{channel}/notice'

        if command == 'nlenergie':
            try:
                parts = text.split()
                verbose = True if len(parts) >= 2 and parts[1] == '-v' else False
                headers = { 'User-Agent': 'GHBot' }

                r = requests.get('http://stofradar.nl:9001/energy/latest', timeout=10, headers=headers)

                try:
                    j = json.loads(r.content.decode('ascii'))

                    t = j['time']

                    prev_j = j

                except Exception as e:
                    j = prev_j

                    t = j['time']

                out = ''
                outblocks = ''
                outblocks_l = ''

                for source in j['mix']:
                    if out != '':
                        out += ', '
                        outblocks_l += ', '

                    perc = source['power'] * 100.0 / j['total']
                    not_perc = source['power'] * 40.0 / j['total']

                    if source['id'] == 'solar':
                        color_index = 8

                    elif source['id'] == 'wind':
                        color_index = 12

                    elif source['id'] == 'nuclear':
                        color_index = 9

                    elif source['id'] == 'waste':
                        color_index = 5

                    elif source['id'] == 'other':
                        color_index = 0

                    elif source['id'] == 'fossil':
                        color_index = 15

                    else:
                        color_index = (abs(hash(source['color']) * 9) % 13) + 2

                    out += f"\3{color_index}{source['id']}: {source['power']} megawatt ({perc:.2f}%)"

                    outblocks += f'\3{color_index}'
                    outblocks += '\u2588' * math.ceil(not_perc)

                    outblocks_l += f"\3{color_index}\u2588 {source['id']}"

                ts = netherlands_tz.localize(datetime.datetime.fromtimestamp(t))

                out += f' ({ts})'

                if verbose:
                    client.publish(response_topic, outblocks + f' ({ts} / {outblocks_l})')

                else:
                    client.publish(response_topic, out)

            except Exception as e:
                client.publish(response_topic, f'Exception during "nlenergie": {e}, line number: {e.__traceback__.tb_lineno}')

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
