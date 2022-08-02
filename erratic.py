#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import requests
import threading
import time
from datetime import timedelta


mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']
prefix       = '!'


def most_busy_vm(data):
    vms = []

    for item in data['proxmox']:
        if item['type'] == "lxc" or item['type'] == "qemu" and item['status'] == "running":
            vms.append({"name": item['name'], "cpu": item['cpu']})

    return sorted(vms, reverse=True, key=lambda v: v['cpu'])

def get_erratic():
    data = requests.get("http://10.208.30.70:8881/").json()
    
    return "Erratic - CPU: %s | Load: %s, %s, %s | Uptime: %s | Mem: u:%s/a:%s (%s) | iowait: %s | Cpu temp: %sc | vmbr0: %s MB/s / %s MB/s | vmbr1: %s MB/s / %s MB/s | Busiest: %s (%s) | LXCs: %s KVMs: %s" % (str(data['cpu']['total']) + "%", data['loadavg'][0], data['loadavg'][1], data['loadavg'][1], "{}".format(str(timedelta(seconds=data['uptime']))), data['memory']['used'], data['memory']['available'], str(data['memory']['percent_used']) + "%", str(data['times']['iowait']) + "%", data['temps']['coretemp'][0][1], data['nic'][0]['vmbr0']['in'], data['nic'][0]['vmbr0']['out'], data['nic'][1]['vmbr1']['in'], data['nic'][1]['vmbr1']['out'], most_busy_vm(data)[0]['name'], str(round(most_busy_vm(data)[0]['cpu']*100, 3)) + "%", data['proxmox_types']['lxc'], data['proxmox_types']['qemu'])

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=erratic|descr=Doorbell statistics')

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
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    if text[0] != prefix:
        return

    command = text[1:].split(' ')[0]

    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/notice'

        if command == 'erratic':
            client.publish(response_topic, get_erratic())

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
