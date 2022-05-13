#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import threading
import time

mqtt_server  = '192.168.64.1'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'test']

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=zorgverzekering|descr=Hulp bij de keuze van een zorgverzekering.')
    client.publish(target_topic, 'cmd=z|descr=Aankondiging van uitschakeling der neocortex for enige tijd.')
    client.publish(target_topic, 'cmd=test|descr=Werkt deze dingetje?')
    client.publish(target_topic, 'cmd=quit|descr=Afsluiten')
    client.publish(target_topic, 'cmd=oens|descr=eh...')

def on_message(client, userdata, message):
    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    parts = topic.split('/')
    channel = parts[2]
    nick = parts[3]

    print(channel, nick, text)

    if channel in channels:
        if text[1:16] == 'zorgverzekering':
            client.publish(f'{topic_prefix}to/irc/{channel}/privmsg', 'Het beste neem je een zorgverzekering die je ziektekosten afdekt.')

        elif text[1:] == 'z':
            client.publish(f'{topic_prefix}to/irc/{channel}/privmsg', 'Truste!')

        elif text[1:] == 'test':
            client.publish(f'{topic_prefix}to/irc/{channel}/privmsg', 'Deze dingetje werks.')

        elif text[1:] == 'quit':
            client.publish(f'{topic_prefix}to/irc/{channel}/privmsg', 'NOOID!')

        elif text[1:] == 'oens':
            client.publish(f'{topic_prefix}to/irc/{channel}/privmsg', 'OENS OENS OENS')

        else:
            print('No match for', text)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f'{topic_prefix}from/irc/#')

client = mqtt.Client()
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")
client.on_message = on_message
client.on_connect = on_connect

announce_commands(client)

client.loop_forever()
