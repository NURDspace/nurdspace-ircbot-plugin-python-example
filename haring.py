#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import threading
import time
import sys

mqtt_server  = 'mqtt.vm.nurd.space'   # TODO: hostname of MQTT server
topic_prefix = 'GHBot/'  # leave this as is
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']  # TODO: channels to respond to
prefix       = '!'  # !command, will be updated by ghbot

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    # TODO: one or more of these:
    client.publish(target_topic, 'cmd=haring|descr=Gief haring')
    client.publish(target_topic, 'cmd=bonk|descr=bonk someone')
    client.publish(target_topic, 'cmd=bonk|descr=bonk someone')
    # you can add |agrp=groupname

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

    tokens = text[1:].split(' ')

    if len(tokens) == 2:
        command = tokens[0]
        recipient = tokens[1]
        sender = nick.split('!')[0]
        give_haring_to_someone = True
    else:
        command = tokens[0]
        recipient = nick.split('!')[0]
        give_haring_to_someone = False

    print(command)

    if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        # TODO: implementation of each command
        if command == 'haring':
            if give_haring_to_someone:
                client.publish(response_topic, 'Hier {0}, een haring! Aangeboden door {1}'.format(recipient, sender))
            else:
                client.publish(response_topic, 'Hier {0}, een haring!'.format(recipient))
        elif command == "bonk":
            client.publish(response_topic, f"Bonks {recipient}! Go to horny jail!")
        elif command == "gewoon--":
            client.publish(response_topic, f"gewoon++")

def on_connect(client, userdata, flags, rc):
    client.subscribe(f'{topic_prefix}from/irc/#')

    client.subscribe(f'{topic_prefix}from/bot/command')

def announce_thread(client):
    while True:
        try:
            announce_commands(client)

            time.sleep(4.1)

        except Exception as e:
            print(f'Failed to announce: {e}')

client = mqtt.Client(sys.argv[0], clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

t = threading.Thread(target=announce_thread, args=(client,))
t.start()

client.loop_forever()
