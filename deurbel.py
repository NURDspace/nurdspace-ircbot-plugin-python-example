#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import json
import paho.mqtt.client as mqtt
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurds']
prefix       = '!'

last_ring    = None

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=doorbell|descr=Doorbell statistics')

def on_message(client, userdata, message):
    global last_ring
    global prefix

    text = message.payload.decode('utf-8')

    if message.topic == 'deurbel':
        last_ring = time.ctime()

        for channel in channels:
            announce_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

            client.publish(announce_topic, '*** DOORBELL ***')

        return

    # space/door/front {"name":"tahtkev","date":"zondag 10 juli 2022","time":"15:29:36","msg":"Toegang verleend - met kaart","cardnr":666}
    if message.topic == 'space/door/front':
        try:
            j = json.loads(text)

            msg = f'--- {j["name"]} opened the door ---'

            for channel in channels:
                announce_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

                client.publish(announce_topic, msg)

        except Exception as e:
            print(f'Failed to announce entry: {e}, line number: {e.__traceback__.tb_lineno}')

        return

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

        if command == 'doorbell':
            if last_ring == None:
                client.publish(response_topic, 'The doorbell never rang')

            else:
                client.publish(response_topic, f'Last ring: {last_ring}')

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f'{topic_prefix}from/irc/#')

        client.subscribe(f'{topic_prefix}from/bot/command')

        client.subscribe(f'deurbel')

        client.subscribe(f'space/door/front')

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
