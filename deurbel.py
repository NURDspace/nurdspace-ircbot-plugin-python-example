#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']

last_ring    = None

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=doorbell|descr=Doorbell statistics')

def on_message(client, userdata, message):
    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    if topic == 'deurbel':
        for channel in channels:
            announce_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

            client.publish(announce_topic, '*** DOORBELL ***')

        return

    parts = topic.split('/')
    channel = parts[2]
    nick = parts[3]

    command = text[1:].split(' ')[0]

    print(channel, command)

    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'doorbell':
            if last_ring == None:
                client.publish(response_topic, 'The doorbell never rang')

            else:
                client.publish(response_topic, 'Last ring: {last_ring}')

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f'{topic_prefix}from/irc/#')

        client.subscribe(f'{topic_prefix}from/bot/command')

        client.subscribe(f'deurbel')

client = mqtt.Client()
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")
client.on_message = on_message
client.on_connect = on_connect

announce_commands(client)

client.loop_forever()
