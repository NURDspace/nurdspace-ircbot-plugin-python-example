#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import random
import threading
import time

mqtt_server  = '192.168.64.1'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'test']


choices      = []

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=zorgverzekering|descr=Hulp bij de keuze van een zorgverzekering.')
    client.publish(target_topic, 'cmd=z|descr=Aankondiging van uitschakeling der neocortex for enige tijd.')
    client.publish(target_topic, 'cmd=test|descr=Werkt deze dingetje?')
    client.publish(target_topic, 'cmd=quit|descr=Afsluiten')
    client.publish(target_topic, 'cmd=oens|descr=Eh...')
    client.publish(target_topic, 'cmd=choose|descr=Choose between comma seperated choices.')
    client.publish(target_topic, 'cmd=secondopinion|descr=Eh...')

def on_message(client, userdata, message):
    global choices

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
        command = text[1:].split(' ')[0]

        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'zorgverzekering':
            client.publish(response_topic, 'Het beste neem je een zorgverzekering die je ziektekosten afdekt.')

        elif command == 'z':
            client.publish(response_topic, 'Truste!')

        elif command == 'test':
            client.publish(response_topic, 'Deze dingetje werks.')

        elif command == 'quit':
            client.publish(response_topic, 'NOOID!')

        elif command == 'oens':
            client.publish(response_topic, 'OENS OENS OENS')

        elif command == 'choose':
            choices = ' '.join(text.split(' ')[1:]).split(',')

            client.publish(response_topic, random.choice(choices))

        elif command == 'secondopinion':
            if len(choices) == 0:
                client.publish(response_topic, 'Nothing to choose from')

            else:
                client.publish(response_topic, random.choice(choices))

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
