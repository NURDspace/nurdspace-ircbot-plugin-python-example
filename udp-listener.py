#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import socket
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'   # TODO: hostname of MQTT server
topic_prefix = 'GHBot/'  # leave this as is
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']  # TODO: channels to respond to

def listener(client):
    try:
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        s.bind(('0.0.0.0', 9393))

        while True:
            message, address = s.recvfrom(512)

            message = message.decode('ascii')

            for channel in channels:
                announce_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

                client.publish(announce_topic, message)

    except Exception as e:
        print(e)

client = mqtt.Client()
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

t = threading.Thread(target=listener, args=(client,))
t.start()

client.loop_forever()
