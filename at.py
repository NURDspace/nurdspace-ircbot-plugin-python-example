#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'
# pip3 install pytz

import datetime
import paho.mqtt.client as mqtt
import pytz
import sqlite3
import threading
import time

mqtt_server    = 'mqtt.vm.nurd.space'
topic_prefix   = 'GHBot/'
channels       = ['nurdbottest', 'nurds', 'nurdsbofh']
db_file        = 'at.db'
prefix         = '!'
netherlands_tz = pytz.timezone("Europe/Amsterdam")

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

    client.publish(target_topic, 'cmd=at|descr=Store a reminder (either "DD/MM/YYYY" or "HH:MM:SS" or those two combined)')

def sleeper(dt, response_topic, txt):
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

    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        tokens  = text.split(' ')

        command = tokens[0][1:]

        if command == 'at' and tokens[0][0] == prefix and len(tokens) >= 3:
            try:
                dt_now = datetime.datetime.now()

                time_offset = 1
                text_offset = 2

                date_string = None
                time_string = '12:00:00'

                if '-' in tokens[1] or '/' in tokens[1]:
                    time_offset = 2
                    text_offset = 3

                    date_string = tokens[1]

                    if '-' in date_string:
                        date_string = date_string.replace('-', '/')

                if ':' in tokens[time_offset]:
                    time_string = tokens[time_offset]

                    if len(time_string) == 5:
                        time_string += ':00'

                else:
                    text_offset = 2

                what = ' '.join(tokens[text_offset:]) + f' ({nick})'

                if date_string == None:
                    date_string = dt_now.strftime('%d/%m/%Y')

                event_time     = netherlands_tz.localize(datetime.datetime.strptime(date_string + " " + time_string, '%d/%m/%Y %H:%M:%S')).timestamp()

                t_now = time.time()

                if event_time < t_now:
                    event_time += 86400

                    date_string = 'tomorrow'

                cur = con.cursor()

                try:
                    cur.execute("INSERT INTO at(channel, `when`, what) VALUES(?, DATETIME(?, 'unixepoch', 'localtime'), ?)", (channel, event_time, what))

                    reminder_str = f'Reminder ({date_string} {time_string}): {what}'

                    client.publish(response_topic, f'Reminder stored for {date_string} {time_string}')

                    sleep_t      = event_time - t_now

                    t = threading.Thread(target=sleeper, args=(sleep_t, response_topic, reminder_str))
                    t.daemon = True
                    t.start()

                except Exception as e:
                    client.publish(response_topic, f'Failed to remember reminder: {e}')

                cur.close()
                con.commit()

            except Exception as e:
                client.publish(response_topic, f'Failed to remember reminder: {e}')

def start_reminder_threads(con):
    global db_file

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

t1 = threading.Thread(target=announce_thread, args=(client,))
t1.start()

start_reminder_threads(con)

client.loop_forever()
