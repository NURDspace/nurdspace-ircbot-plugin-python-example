#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'
# also python-mpd2 is required (via pip)

import math
from mpd import MPDClient
import paho.mqtt.client as mqtt
import threading
import time


import socket
import sys
mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'test', 'nurdsbofh']
mpd_server   = 'spacesound.vm.nurd.space'
mpd_port     = 6600
prefix       = '!'

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=play|descr=Start playing.')
    client.publish(target_topic, 'cmd=stop|descr=Stop playing.')
    client.publish(target_topic, 'cmd=next|descr=Skip to the next track.')
    client.publish(target_topic, 'cmd=pause|descr=Stops the music, or unstops it.')
    client.publish(target_topic, 'cmd=prev|descr=Skip to the previous track.')
#    client.publish(target_topic, 'cmd=np|descr=What is playing right now?')
    client.publish(target_topic, 'cmd=clearpl|descr=Clear the current playlist.')
    client.publish(target_topic, 'cmd=mpdsearch|descr=Search for a song, by title keywords.')
    client.publish(target_topic, 'cmd=mpdadd|descr=Add a song(s) to the current play queue. Searches by title keyword(s).')

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

def group_results(in_):
    out  = ''

    seen = set()

    for result in in_:
        if 'artist' in result and 'title' in result:
            to_add = '\2' + result['artist'] + '\2: ' + result['title']

            temp   = to_add.lower()

            if temp in seen:
                continue

            seen.add(temp)

            if out != '':
                out += ', '

            out += to_add

            if len(out) > 350:
                break

    return out

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

    if (channel in channels or channel[0] == '\\') and command in ['next', 'np', 'prev', 'pause', 'clearpl', 'play', 'stop', 'mpdsearch', 'mpdadd']:
        response_topic = f'{topic_prefix}to/irc/{channel}/notice'

        try:
            mpd_client = MPDClient()
            mpd_client.connect(mpd_server, mpd_port)

            current_song = mpd_client.currentsong()

            status = mpd_client.status()

            playing = gen_song_name(current_song)

            if command == 'next':
                mpd_client.next()

                now_current_song = mpd_client.currentsong()
                now_playing = gen_song_name(now_current_song)

                client.publish(response_topic, f'Skipped {playing}, now playing: {now_playing}')

            elif command == 'prev':
                mpd_client.previous()

                client.publish(response_topic, f'Went back to the previous song')

            elif command == 'play':
                mpd_client.pause(0)

                client.publish(response_topic, f'The music should be playing now')

            elif command == 'stop':
                mpd_client.pause(1)

                client.publish(response_topic, f'The music should be stopped now')

            elif command == 'mpdsearch' or command == 'mpdadd':
                space = text.find(' ')

                if space != -1:
                    if command == 'mpdsearch':
                        results = mpd_client.search('title', text[space + 1:])

                        out = group_results(results)

                        if len(out) < 350:
                            results = mpd_client.search('artist', text[space + 1:])

                            temp = group_results(results)

                            if temp != '':
                                if out != '':
                                    out += ' | '

                                out += temp

                                if len(out) > 350:
                                    out = out[0:350]

                        if out == '':
                            client.publish(response_topic, 'No such song found')

                        else:
                            client.publish(response_topic, 'Results: ' + out)

                    elif command == 'mpdadd':
                        mpd_client.searchadd('title', text[space + 1:])

                        client.publish(response_topic, 'Some song(s) might have been added to the play queue')

                else:
                    client.publish(response_topic, 'Parameter missing')

            elif command == 'pause':
                mpd_client.pause()

                status = mpd_client.status()

                if status["state"] == 'play':
                    client.publish(response_topic, f'The music is unpaused')

                else:
                    client.publish(response_topic, f'The music is paused')

            elif command == 'clearpl':
                mpd_client.clear()
                mpd_client.pause(1)

                client.publish(response_topic, f'The playlist has been cleared (and paused)')

#            elif command == 'np':
#                duration = float(status['duration'])
#                elapsed  = float(status['elapsed'])

#                finished_percentage = elapsed * 100 / duration

#                time_left = duration - elapsed

#                light_meters = 299792458 * time_left

#                client.publish(response_topic, f'Now playing: {playing} ({100 - finished_percentage:.2f}% left or {time_left:.2f} seconds or the time that light moves {light_meters / 1000:.2f} meters)')

            mpd_client.close()

            mpd_client.disconnect()

        except Exception as e:
            print(f'Exception: {e}, line number: {e.__traceback__.tb_lineno}')

            client.publish(response_topic, f'mpd: {e}')

def on_connect(client, userdata, flags, rc):
    client.subscribe(f'{topic_prefix}from/irc/#')

    client.subscribe(f'{topic_prefix}from/bot/command')

def announce_thread(client):
    while True:
        try:
            announce_commands(client)

            time.sleep(4.1)

        except Exception as e:
            print(f'Failed to announce: {e}')

client = mqtt.Client(f'{socket.gethostname()}_{sys.argv[0]}', clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

t = threading.Thread(target=announce_thread, args=(client,))
t.start()

client.loop_forever()
