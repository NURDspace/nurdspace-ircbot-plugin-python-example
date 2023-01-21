#! /usr/bin/python3

import paho.mqtt.client as mqtt
import threading
import time
import sys
import random

mqtt_server  = 'mqtt.vm.nurd.space'   # TODO: hostname of MQTT server
topic_prefix = 'GHBot/'  # leave this as is
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']  # TODO: channels to respond to

def on_message(client, userdata, message):
    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if len(text) == 0:
        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'  # default channel if can't be deduced
    hostmask = parts[3] if len(parts) >= 4 else 'jemoeder'  # default nick if it can't be deduced
    nickname = hostmask.split('!')[0]

    message_response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'
    karma_command_topic = f'{topic_prefix}from/irc/{channel}/{hostmask}/message'

    if text == 'gewoon--':
        time.sleep(random.randint(1,3))
        client.publish(message_response_topic, f"gewoon++")
        client.publish(karma_command_topic, f'gewoon++')

def on_connect(client, userdata, flags, rc):
    client.subscribe(f'{topic_prefix}from/irc/#')


client = mqtt.Client(sys.argv[0], clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

client.loop_forever()
