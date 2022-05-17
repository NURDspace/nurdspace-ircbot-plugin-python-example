#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

# ping3 from pip

import paho.mqtt.client as mqtt
from ping3 import ping
import threading
import time


mqtt_server  = '192.168.64.1'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'test']

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=ping|descr=Perform ping (ICMP request) on $parameter.')

def on_message(client, userdata, message):
    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    parts = topic.split('/')
    channel = parts[2]
    nick = parts[3]

    if channel in channels:
        tokens  = text.split(' ')

        command = tokens[0][1:]

        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'ping':
            if len(tokens) == 2:
                host = tokens[1]
                time = ping(host, unit='ms')

                client.publish(response_topic, f'Pinging {host} took {time:.2f} milliseconds')

            else:
                client.publish(response_topic, 'Invalid number of parameters for ping.')

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f'{topic_prefix}from/irc/#')

        client.subscribe(f'{topic_prefix}from/bot/command')

client = mqtt.Client()
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")
client.on_message = on_message
client.on_connect = on_connect

announce_commands(client)

client.loop_forever()
