#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import psycopg2
import threading
import time
import traceback

# based on https://github.com/NURDspace/PartKeepr-CLI

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']
prefix       = '!'

pk_db_user     = 'partkeepr'
pk_db_password = 'partkeepr'
pk_db_db       = 'partkeepr'
pk_db_host     = '10.208.11.210'

def search_partkeepr(what):
    conn = psycopg2.connect(host=pk_db_host, database=pk_db_db, user=pk_db_user, password=pk_db_password, port=5432)

    cur = conn.cursor()

    cur.execute("SELECT part.name, storagelocation.name FROM part, storagelocation WHERE part.storagelocation_id = storagelocation.id AND (part.name ILIKE '%%' || %s || '%%' OR part.description ILIKE '%%' || %s || '%%')", (what, what,))

    out = ''
    cnt = 0

    for row in cur:
        if out != '':
            out += ', '

        out += f'{row[0]}: \2{row[1]}\2'

        cnt += 1

        if cnt >= 50:
            break

    conn.close()

    return out

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=pklocate|descr=Locate in partkeepr')

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
        response_topic = f'{topic_prefix}to/irc/{channel}/notice'

        if command == 'pklocate':
            try:
                what    = ' '.join(text.split(' ')[1:])

                results = search_partkeepr(what)

                if results == '':
                    client.publish(response_topic, f'"{what}" not found in partkeepr')

                else:
                    client.publish(response_topic, results)

            except Exception as e:
                print(traceback.format_exception(type(e), e, e.__traceback__))

                client.publish(response_topic, f'Partkeepr plugin: {e}')

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
