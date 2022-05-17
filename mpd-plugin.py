#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'
# also python-mpd2 is required (via pip)

from mpd import MPDClient
import paho.mqtt.client as mqtt
import threading
import time

mqtt_server  = '192.168.64.1'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'test']
mpd_server   = 'spacesound.vm.nurd.space'
mpd_port     = 6600

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=next|descr=Skip to the next track.')
    client.publish(target_topic, 'cmd=prev|descr=Skip to the previous track.')
    client.publish(target_topic, 'cmd=np|descr=What is playing right now?')

def on_message(client, userdata, message):
    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    parts = topic.split('/')
    channel = parts[2]
    nick = parts[3]

    command = text[1:].split(' ')[0]

    if channel in channels and command in ['next', 'np', 'prev']:

        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        try:
            mpd_client = MPDClient()
            mpd_client.connect(mpd_server, mpd_port)

            current_song = mpd_client.currentsong()

            if command == 'next':
                mpd_client.next()

                client.publish(response_topic, f'Skipped {current_song}')

            elif command == 'prev':
                mpd_client.previous()

                client.publish(response_topic, f'Went back to the previous song')

            elif command == 'np':
                client.publish(response_topic, f'Now playing: {current_song}')

            mpd_client.close()

            mpd_client.disconnect()

        except Exception as e:
            client.publish(response_topic, f'mpd: {e}')

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
