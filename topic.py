#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import threading
import time


import socket
import sys
mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh', 'nurds-dream']
prefix       = '!'
topics       = [None, None, None, None]  # as many elements as in the 'channels' list (above)

last_state   = None

first        = True

def log(str_):
    try:
        fh = open('/home/ghbot/topic.log', 'a+')
        fh.write(f'{str_}\n')
        fh.close()

        print(str_)

    except Exception as e:
        print(f'log error: {e}, line number: {e.__traceback__.tb_lineno}')

def announce_commands():
    global mqtt_server

    target_topic = f'{topic_prefix}to/bot/register'

    publish.single(target_topic, hostname=mqtt_server, payload='cmd=cleartopic|descr=Remove all text from topic')
    publish.single(target_topic, hostname=mqtt_server, payload='cmd=settopic|descr=Remove all text from topic and replace it by something new')
    publish.single(target_topic, hostname=mqtt_server, payload='cmd=addtopic|descr=Add a text to the existing topic')
    publish.single(target_topic, hostname=mqtt_server, payload='cmd=deltopic|descr=Delete an entry from the topic matching the given text')

def set_topic(channel_nr, text):
    global last_state
    global topics

    if text[0:9] == 'Space is ':
        pipe = text.find('|')

        if pipe != -1:
            text = text[pipe + 1:].strip()

    text = 'Space is ' + ('OPEN' if last_state.lower() == 'true' else 'closed') + ' | ' + text

    print('OLD', topics[channel_nr])
    print('NEW', text)

    if text != topics[channel_nr]:
        client.publish(f'{topic_prefix}to/irc/{channels[channel_nr]}/topic', text)

        topics[channel_nr] = text

def on_message(client, userdata, message):
    global last_state
    global prefix

    text = message.payload.decode('utf-8')

    print(message.topic, text)

    if message.topic == 'space/state':
        try:
            if text != last_state:
                last_state = text

                log(f'state changed to {text}')

                for i in range(0, len(channels)):
                    if topics[i] != None:
                        set_topic(i, topics[i])

        except Exception as e:
            log(f'space/stagedigit error: {e}, line number: {e.__traceback__.tb_lineno}')

        return

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands()

        return

    if topic == 'from/bot/parameter/prefix':
        prefix = text

        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    try:
        # why?! TODO
        channel_nr = channels.index(channel)

    except ValueError as ve:
        channel_nr = -1

    command = None
    if text != '' and text[0] == prefix:
        command = text[1:].split(' ')[0]

    print(channel, command, text)

    if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
        if len(parts) >= 4 and parts[3] == 'topic':
            set_topic(channel_nr, text)

            log(f'{nick} set {channel} to {text} ({topics[channel_nr]})')

        elif command == 'cleartopic':
            set_topic(channel_nr, '')

        elif command == 'settopic':
            new_topic = text.split()

            if len(new_topic) > 1:
                set_topic(channel_nr, ' '.join(new_topic[1:]))

        elif command == 'addtopic':
            try:
                new_topic = text.split()

                if len(new_topic) > 1:
                    text = ('' if topics[channel_nr] == None else topics[channel_nr]).strip()

                    if text != '' and text[-1] != '|':
                        text += ' | '

                    elif text != '' and text[-1] == '|':
                        text += ' '

                    text += f'{" ".join(new_topic[1:])}'

                    # log(text)

                    print(f'adding "{new_topic}" to topic: {text}')

                    set_topic(channel_nr, text)

            except Exception as e:
                log(f'addtopic error: {e}, line number: {e.__traceback__.tb_lineno}')

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

                    text =  ' | '.join(parts).strip()

                    if text[-1] != '|':
                        text += ' |'

                    print(f'set topic after del to "{text}"')

                    set_topic(channel_nr, text)

                else:
                    log('deltopic', input_, topics[channel_nr])

            except Exception as e:
                log(f'deltopic error: {e}, line number: {e.__traceback__.tb_lineno}')

def on_connect(client, userdata, flags, rc):
    global first

    try:
        client.subscribe(f'{topic_prefix}from/irc/#')

        client.subscribe(f'{topic_prefix}from/bot/command')

        client.subscribe(f'space/state')

    except Exception as e:
        log(f'on_connect error: {e}, line number: {e.__traceback__.tb_lineno}')

    first = True

def announce_thread():
    global first
    global mqtt_server

    while True:
        try:
            announce_commands()

            if first:
                first = False

                target_topic = f'{topic_prefix}to/bot/request'

                print(f'requesting topics ({target_topic})')

                publish.single(target_topic, hostname=mqtt_server, payload='topics')

            time.sleep(4.1)

        except Exception as e:
            log(f'Failed to announce: {e}')

client = mqtt.Client(f'{socket.gethostname()}_{sys.argv[0]}', clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

t = threading.Thread(target=announce_thread)
t.start()

client.loop_forever()
