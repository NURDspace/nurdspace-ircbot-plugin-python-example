#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'
# pip3 install dateparser
# pip3 install pytz

import dateparser
import datetime
import paho.mqtt.client as mqtt
import pytz
import sqlite3
import threading
import time

import socket
import sys

print('Init...')

mqtt_server    = 'mqtt.vm.nurd.space'
topic_prefix   = 'GHBot/'
channels       = ['nurdbottest', 'nurds', 'nurdsbofh']
db_file        = 'at.db'
prefix         = '!'
netherlands_tz = pytz.timezone("Europe/Amsterdam")

print('Init DB...')
con = sqlite3.connect(db_file)

cur = con.cursor()
try:
    cur.execute('CREATE TABLE at(channel TEXT NOT NULL, `when` DATETIME NOT NULL, what TEXT NOT NULL)')

    cur.execute('CREATE INDEX at_when ON at(`when`)')

except sqlite3.OperationalError as oe:
    # should be "table already exists"
    pass

cur.close()

cur = con.cursor()
cur.execute('PRAGMA journal_mode=wal')
cur.close()

con.commit()

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=at|descr=Store a reminder (either "DD-MM-YYYY" or "HH:MM:SS" or those two combined)')
    client.publish(target_topic, 'cmd=date|descr=Emit current date/time')

def sleeper(dt, response_topic, txt):
    if dt > 0:
        time.sleep(dt)

    client.publish(response_topic, txt)

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

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
        response_topic = f'{topic_prefix}to/irc/{channel}/notice'

        tokens  = text.split()

        command = tokens[0][1:]

        if command == 'at' and tokens[0][0] == prefix and len(tokens) >= 3:
            try:
                input_    = tokens[1].replace('/', '-')
                input_idx = 2

                final_d   = None

                while True:
                    d = dateparser.parse(input_)

                    if d == None:
                        break

                    final_d    = d

                    input_    += ' ' + tokens[input_idx]
                    input_idx += 1

                if final_d == None:
                    client.publish(response_topic, f'Cannot parse time-string {input_}')

                    return

                what       = ' '.join(tokens[1:])

                event_time = final_d.timestamp()

                t_now      = time.time()

                while event_time < t_now:
                    final_d    += datetime.timedelta(hours=24)
                    event_time += 86400

                cur = con.cursor()

                try:
                    cur.execute("INSERT INTO at(channel, `when`, what) VALUES(?, DATETIME(?, 'unixepoch', 'localtime'), ?)", (channel, event_time, what))

                    ts_string    = final_d.strftime('%Y-%m-%d %H:%M:%S (%A)')

                    reminder_str = f'Reminder ({ts_string}): {what}'

                    client.publish(response_topic, f'Reminder stored for {ts_string}')

                    sleep_t      = event_time - t_now

                    t = threading.Thread(target=sleeper, args=(sleep_t, response_topic, reminder_str))
                    t.daemon = True
                    t.start()

                except Exception as e:
                    client.publish(response_topic, f'Failed to remember reminder: {e}, line number: {e.__traceback__.tb_lineno}')

                cur.close()
                con.commit()

            except Exception as e:
                client.publish(response_topic, f'Failed to remember reminder: {e}, line number: {e.__traceback__.tb_lineno}')

        elif command == 'date':
            client.publish(response_topic, f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S (Bertrik/buZz dat is %A)")}')

def start_reminder_threads(con):
    global db_file

    print('Loading reminders...')

    con = sqlite3.connect(db_file)

    cur = con.cursor()
    cur.execute('SELECT channel, `when` AS "datetime [timestamp]", what, datetime("now", "localtime") FROM at WHERE `when` > datetime("now", "localtime") ORDER BY `when` ASC LIMIT 1')
    rows = cur.fetchall()
    cur.close()

    for row in rows:
        channel    = row[0]

        next_event = netherlands_tz.localize(datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')).timestamp()

        now        = time.time()

        sleep_t    = next_event - now

        if sleep_t >= 0:
            response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

            ts_str         = row[1]

            reminder_str   = f'Reminder ({ts_str}): {row[2]}'

            t = threading.Thread(target=sleeper, args=(sleep_t, response_topic, reminder_str))
            t.daemon = True
            t.start()

    con.close()

def on_connect(client, userdata, flags, rc):
    try:
        client.subscribe(f'{topic_prefix}from/irc/#')

        client.subscribe(f'{topic_prefix}from/bot/command')

    except Exception as e:
        log(f'on_connect error: {e}, line number: {e.__traceback__.tb_lineno}')

def announce_thread(client):
    while True:
        try:
            announce_commands(client)

            time.sleep(4.1)

        except Exception as e:
            print(f'Failed to announce: {e}')

            time.sleep(1.0)

print('Connect to mqtt...')

client = mqtt.Client(f'{socket.gethostname()}_{sys.argv[0]}', clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

t1 = threading.Thread(target=announce_thread, args=(client,))
t1.start()

start_reminder_threads(con)

print('Go!')

client.loop_forever()
