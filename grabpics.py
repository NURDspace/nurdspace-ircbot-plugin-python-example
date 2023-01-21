#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import socket
import sys
import threading
import time
from urlextract import URLExtract

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh', 'nurds-dream']
prefix       = '!'

def on_message(client, userdata, message):
    try:
        text = message.payload.decode('utf-8')

        topic = message.topic[len(topic_prefix):]

        parts   = topic.split('/')
        channel = parts[2] if len(parts) >= 3 else 'nurds'

        if channel[0] != '\\':
            extractor = URLExtract()

            urls = extractor.find_urls(text)

            for url in urls:
                print(time.ctime(), url)
                publish.single(f'irc/urls/{channel}', url, hostname=mqtt_server)

    except Exception as e:
        log(f'on_message error: {e}, line number: {e.__traceback__.tb_lineno}')

def on_connect(client, userdata, flags, rc):
    try:
        client.subscribe(f'{topic_prefix}from/irc/#')
        client.subscribe(f'{topic_prefix}to/irc/#')

    except Exception as e:
        log(f'on_connect error: {e}, line number: {e.__traceback__.tb_lineno}')

client = mqtt.Client(f'{socket.gethostname()}_{sys.argv[0]}', clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

client.loop_forever()
