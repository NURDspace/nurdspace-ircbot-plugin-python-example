#! /usr/bin/python3

import json
import os
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import time

map_ = dict()

seen = dict()

def on_message(client, userdata, message):
    try:
        j = json.loads(message.payload)

        print(j)

        if 'payload' in j and 'from' in j and 'text' in j['payload'] and j['to'] == -1:
            hash_ = hash(f"{j['from']} {j['id']} {j['payload']['text']}")
            
            now = time.time()

            if hash_ in seen:
                if now - seen[hash_] < 30:
                    print('ignoring message')
                    return

            seen[hash_] = now

            sender = f'{j["from"] & 0xffffffff:08x}'

            name = map_[sender] if sender in map_ else sender

            msg = 'Meshtastic: ' + j['payload']['text'] + f' ({name})'

            topic_prefix = 'GHBot/'
            channel = 'nurds'

            response_topic_pm = f'{topic_prefix}to/irc/{channel}/privmsg'

            print(f'Sending "{msg}" to "{response_topic_pm}"')

            publish.single(response_topic_pm, msg, hostname='mqtt.vm.nurd.space')

        # {'channel': 0, 'from': -1851658976, 'id': 1236532832, 'payload': {'hardware': 3, 'id': '!91a1ed20', 'longname': 'fvh', 'shortname': 'fvh'},
        # 'sender': '!91a1e97c', 'timestamp': 1674387014, 'to': 986987176, 'type': 'nodeinfo'}

        elif 'payload' in j and 'id' in j['payload'] and 'longname' in j['payload']:
            print(f'{j["payload"]["id"]} is {j["payload"]["longname"]}')

            id_ = j['payload']['id']
            if id_[0] == '!':
                id_ = id_[1:]

            map_[id_] = j['payload']['longname']

    except Exception as e:
        print(f'on_message: {e}, line number: {e.__traceback__.tb_lineno}')

def on_connect(client, userdata, flags, rc):
    print(client, userdata, flags, rc)

    client.subscribe('msh/2/json/NurdSpace/#')

client = mqtt.Client('jabla%d', os.getpid())
client.connect('10.208.30.67', port=1883, keepalive=60)
client.on_message = on_message
client.on_connect = on_connect
client.loop_forever()
