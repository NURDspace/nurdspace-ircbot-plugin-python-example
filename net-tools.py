#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

# ping3 from pip
# ntplib from pip

import ntplib
import paho.mqtt.client as mqtt
from ping3 import ping
import threading
from time import ctime


mqtt_server  = '192.168.64.1'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'test']

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=ping|descr=Perform ping (ICMP request) on $parameter.')
    client.publish(target_topic, 'cmd=time|descr=What point on the vector of time are we right now.')

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

                if time == None:
                    client.publish(response_topic, f'Cannot ping {host} because of an unknown reason')

                else:
                    client.publish(response_topic, f'Pinging {host} took {time:.2f} milliseconds')

            else:
                client.publish(response_topic, 'Invalid number of parameters for ping.')

        elif command == 'time':
            try:
                t        = ntplib.NTPClient()

                response = t.request('myip.vanheusden.com', version=3)

                t_string = ctime(response.tx_time)

                client.publish(response_topic, f'It is now +/- {t_string} and the computer this bot-plugin runs on is {response.offset:.3f} seconds off.')

            except Exception as e:
                client.publish(response_topic, f'Failed determining time ({e})')

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
