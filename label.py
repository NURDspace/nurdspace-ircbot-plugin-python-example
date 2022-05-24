#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import os
import paho.mqtt.client as mqtt
import socket
import subprocess
import threading
import time


mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'test', 'nurdsbofh']
prefix       = '!'

host         = 'slabpi.lan.nurd.space'
port         = 22
user         = 'labelprinter'
path         = '/home/labelprinter/nurdbotlabelprinting'
executable   = 'label.sh'    # regular label
bcexecutable = 'bclabel.sh'  # bookcrossing label
qrexecutable = 'qrlabel.sh'  # QR code


def check_host_up(host, port):
    try:
        host_addr = socket.gethostbyname(host)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.settimeout(0.5)

        s.connect((host, port))

        s.close()

    except:
        return False

    return True

def cmd_label(client, response_topic, value):
    if value == None:
        client.publish(response_topic, 'Please provide a text to print')

        return

    response = check_host_up(host, port)

    if response == True:
        try:
            input_ = '0x' + ''.join("{:02x}".format(ord(c)) for c in value)

            client.publish(response_topic, f'Printing: {value}')

            subprocess.call(["ssh", user + "@" + host, path + "/" + executable + " " + input_]);

        except Exception as e:
            client.publish(response_topic, f'Exception during "label": {e}, line number: {e.__traceback__.tb_lineno}')

    else:
        client.publish(response_topic, f'Host {host} is unreachable')

def cmd_bclabel(client, response_topic, value):  # bookcrossing
    response = check_host_up(host, port)

    if response == True:
        if value == None:
            client.publish(response_topic, 'Please provide a book crossing-ID to print')

            return

        input_ = '0x'+''.join("{:02x}".format(ord(c)) for c in value)

        subprocess.call(["ssh", user + "@" + host, path + "/" + bcexecutable + " " + input_]);

        client.publish(response_topic, 'Printing bookcrossing label: ' + value)

    elif response == False:
        client.publish(response_topic, f"l'Hôte {host} n'est pas disponible pour le moment")

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=label|descr=Print een label.')
    client.publish(target_topic, 'cmd=bclabel|descr=Print a book crossing label.')

def on_message(client, userdata, message):
    global choices
    global prefix

    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    if topic == 'from/bot/parameter/prefix':
        prefix = text

        return

    if text[0] != prefix:
        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    parts     = text.split(' ')
    command   = parts[0][1:]
    value     = parts[1]  if len(parts) >= 2 else None
    value_all = parts[1:] if len(parts) >= 2 else None

    if channel in channels:
        command = text[1:].split(' ')[0]

        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'label':
            cmd_label(client, response_topic, ' '.join(value_all) if value_all != None else None)

        elif command == 'bclabel':
            cmd_label(client, response_topic, value)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f'{topic_prefix}from/irc/#')

        client.subscribe(f'{topic_prefix}from/bot/command')

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
