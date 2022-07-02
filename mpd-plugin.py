#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'
# also python-mpd2 is required (via pip)

import math
from mpd import MPDClient
import paho.mqtt.client as mqtt
import threading
import time

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'test', 'nurdsbofh']
mpd_server   = 'spacesound.vm.nurd.space'
mpd_port     = 6600
prefix       = '!'

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=next|descr=Skip to the next track.')
    client.publish(target_topic, 'cmd=pause|descr=Stops the music, or unstops it.')
    client.publish(target_topic, 'cmd=prev|descr=Skip to the previous track.')
    client.publish(target_topic, 'cmd=np|descr=What is playing right now?')
    client.publish(target_topic, 'cmd=clearpl|descr=Clear the current playlist.')

def gen_song_name(song_meta):
    playing = ''

    if 'artist' in song_meta and 'title' in song_meta:
        playing += song_meta['artist'] + ' - ' + song_meta['title']

    else:
        if 'title' in song_meta:
            playing += f' title: {song_meta["title"]}'

        if 'artist' in song_meta:
            playing += f' (artist: {song_meta["artist"]})'

    if 'album' in song_meta:
        playing += f' (album: {song_meta["album"]})'

    if playing.strip() == '' and 'file' in song_meta:
        playing = song_meta['file']

    if 'duration' in song_meta:
        song_meta = float(song_meta['duration'])

        duration_minutes = math.floor(song_meta / 60)

        if math.fmod(song_meta, 60) >= 30:
            playing += f' (takes almost {duration_minutes + 1:.0f} minutes to play)'

        else:
            playing += f' (takes about {duration_minutes:.0f} minutes to play)'

    return playing

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

    if text[0] != prefix:
        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    command = text[1:].split(' ')[0]

    if channel in channels and command in ['next', 'np', 'prev', 'pause', 'clearpl']:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        try:
            mpd_client = MPDClient()
            mpd_client.connect(mpd_server, mpd_port)

            current_song = mpd_client.currentsong()

            status = mpd_client.status()

            playing = gen_song_name(current_song)

            if command == 'next':
                mpd_client.next()

                client.publish(response_topic, f'Skipped {playing}')

            elif command == 'prev':
                mpd_client.previous()

                client.publish(response_topic, f'Went back to the previous song')

            elif command == 'pause':
                mpd_client.pause()

                client.publish(response_topic, f'The music is paused or unpaused')

            elif command == 'clearpl':
                mpd_client.clear()
                mpd_client.pause(1)

                client.publish(response_topic, f'The playlist has been cleared (and paused)')

            elif command == 'np':
                duration = float(status['duration'])
                elapsed  = float(status['elapsed'])

                finished_percentage = elapsed * 100 / duration

                time_left = duration - elapsed

                light_meters = 299792458 * time_left

                client.publish(response_topic, f'Now playing: {playing} ({100 - finished_percentage:.2f}% left or {time_left:.2f} seconds or the time that light moves {light_meters / 1000:.2f} meters)')

            mpd_client.close()

            mpd_client.disconnect()

        except Exception as e:
            client.publish(response_topic, f'mpd: {e}')

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
