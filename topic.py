#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']
prefix       = '!'
topics       = [None, None, None]  # as many elements as in the 'channels' list (above)

last_state   = '0'

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=cleartopic|descr=Remove all text from topic')
    client.publish(target_topic, 'cmd=settopic|descr=Remove all text from topic and replace it by something new')
    client.publish(target_topic, 'cmd=addtopic|descr=Add a text to the existing topic')
    client.publish(target_topic, 'cmd=deltopic|descr=Delete an entry from the topic matching the given text')

def set_topic(channel, text):
    global last_state

    if text[0:9] == 'Space is ':
        pipe = text.find('|')

        if pipe != -1:
            text = text[pipe + 1:].strip()

    text = 'Space is ' + ('OPEN' if last_state == '1' else 'closed') + ' | ' + text

    client.publish(f'{topic_prefix}to/irc/{channel}/topic', text)

def on_message(client, userdata, message):
    global last_state
    global prefix

    text = message.payload.decode('utf-8')

    if message.topic == 'space/statedigit':
        if text != last_state:
            last_state = text

            for i in range(0, len(channels)):
                if topics[i] != None:
                    set_topic(channels[i], topics[i])

        return

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    if topic == 'from/bot/parameter/prefix':
        prefix = text

        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    try:
        channel_nr = channels.index(channel)

    except ValueError as ve:
        channel_nr = -1

    command = None
    if text != '' and text[0] == prefix:
        command = text[1:].split(' ')[0]

    if channel in channels:
        if len(parts) >= 4 and parts[3] == 'topic':
            topics[channel_nr] = text

            print(f'Someone set {channel} to {topics[channel_nr]}')

        elif command == 'cleartopic':
            set_topic(channel, '')

        elif command == 'settopic':
            new_topic = text.split()

            if len(new_topic) > 1:
                set_topic(channel, ' '.join(new_topic[1:]))

        elif command == 'addtopic':
            new_topic = text.split()

            if len(new_topic) > 1:
                if topics[channel_nr] != '':
                    topics[channel_nr] += ' | '

                topics[channel_nr] += f'{" ".join(new_topic[1:])}'

                # print(topics[channel_nr])

                set_topic(channel, topics[channel_nr])

        elif command == 'deltopic':
            try:
                input_ = text.split()

                if len(input_) > 1 and topics[channel_nr] != None:
                    search_text = input_[1].lower()

                    parts = topics[channel_nr].split('|')

                    i = 0

                    while i < len(parts):
                        if search_text in parts[i].lower():
                            parts.pop(i)

                        else:
                            i += 1

                    for i in range(0, len(parts)):
                        parts[i] = parts[i].strip()

                    topics[channel_nr] = ' | '.join(parts)

                    set_topic(channel, topics[channel_nr])

                else:
                    print('deltopic', input_, topics[channel_nr])

            except Exception as e:
                print(f'deltopic error: {e}, line number: {e.__traceback__.tb_lineno}')

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f'{topic_prefix}from/irc/#')

        client.subscribe(f'{topic_prefix}from/bot/command')

        client.subscribe(f'space/statedigit')

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
