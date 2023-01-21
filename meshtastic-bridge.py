#! /usr/bin/python3

import json
import os
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

map_ = dict()

def on_message(client, userdata, message):
    try:
        j = json.loads(message.payload)

        print(j)

        if 'payload' in j and 'sender' in j and 'text' in j['payload']:
            sender = j['sender']

            name = map_[sender] if sender in map_ else sender

            msg = 'Meshtastic: ' + j['payload']['text'] + ' (' + name + ')'

            topic_prefix = 'GHBot/'
            channel = 'nurds'

            response_topic_pm = f'{topic_prefix}to/irc/{channel}/privmsg'

            print(f'Sending "{msg}" to "{response_topic_pm}"')

            publish.single(response_topic_pm, msg, hostname='mqtt.vm.nurd.space')

        elif 'payload' in j and 'id' in j['payload'] and 'longname' in j['payload']:
            map_[j['payload']['id']] = j['payload']['longname']

    except Exception as e:
        print('on_message: {e}, line number: {e.__traceback__.tb_lineno}')

def on_connect(client, userdata, flags, rc):
    print(client, userdata, flags, rc)

    if rc == 0:
        client.subscribe('msh/2/json/NurdSpace/#')

client = mqtt.Client('jabla%d', os.getpid())
client.connect('10.208.30.67', port=1883, keepalive=60)
client.on_message = on_message
client.on_connect = on_connect
client.loop_forever()
