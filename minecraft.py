#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'
# pip3 install mcstatus

from mcstatus import JavaServer
import paho.mqtt.client as mqtt
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']
prefix       = '!'
mc_server    = '10.208.30.188'

last_ring    = None

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=minecraft|descr=Minecraft server statistics')

def on_message(client, userdata, message):
    global last_ring
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
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    if text[0] != prefix:
        return

    command = text[1:].split(' ')[0]

    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'minecraft':
            server = JavaServer(mc_server)

            latency = server.ping()

            query = server.query()

            if len(query.players.names) > 0:
                client.publish(response_topic, f'The server at {mc_server} has the following players online: {", ".join(query.players.names)} and responds in {latency}ms.')

            else:
                client.publish(response_topic, f'The server at {mc_server} has no players on-line currently and responds in {latency}ms.')

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f'{topic_prefix}from/irc/#')

        client.subscribe(f'{topic_prefix}from/bot/command')

        client.subscribe(f'deurbel')

def announce_thread(client):
    while True:
        try:
            announce_commands(client)

            time.sleep(4.1)

        except Exception as e:
            print(f'Failed to announce: {e}')

client = mqtt.Client()
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")
client.on_message = on_message
client.on_connect = on_connect

t = threading.Thread(target=announce_thread, args=(client,))
t.start()

client.loop_forever()
