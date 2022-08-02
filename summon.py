#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'
# pip3 install xmpppy

import paho.mqtt.client as mqtt
import smtplib
import sqlite3
from summoncfg import *
import threading
import time
import xmpp

# create table entities(nick varchar(255) not null primary key, email varchar(255) not null, jabber varchar(255) not null);

mqtt_server  = 'mqtt.vm.nurd.space'   # TODO: hostname of MQTT server
topic_prefix = 'GHBot/'  # leave this as is
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']  # TODO: channels to respond to
prefix       = '!'  # !command, will be updated by ghbot
db           = 'summon.db'

# summoncfg.py should contain:
#xmpp_user = '...jabber account...'
#xmpp_pass = '...jabber account password...'
#xmpp_host = '...ip-address or hostname of xmpp-server to which xmpp_user belongs...'


con = sqlite3.connect(db)

cur = con.cursor()
cur.execute('PRAGMA journal_mode=wal')
cur.close()


def summon(nick, text, by_whom, channel):
    global con

    ok = True

    cur = con.cursor()
    cur.execute('SELECT email, jabber FROM entities WHERE nick=?', (nick,))

    row = cur.fetchone()
    if row == None:
        return False

    email  = row[0]
    jabber = row[1]

    cur.close()

    if email != None:
        sender    = 'ghbot@nurdspace.nl'
        receivers = [email]

        message = f'You ({nick}) were summoned by {by_whom} in {channel}: {text}'

        try:
           smtpObj = smtplib.SMTP('smtp.bit.nl')
           smtpObj.sendmail(sender, receivers, message)

        except SMTPException as e:
           print(f'Exception during "sendmail": {e}, line number: {e.__traceback__.tb_lineno}')

           ok = False

    if jabber != None:
        try:
            tojid = jabber

            jid = xmpp.protocol.JID(xmpp_user)
            cl  = xmpp.Client(jid.getDomain(), debug=[])

            #xcon = cl.connect()
            xcon = cl.connect((xmpp_host, 5222))
            if not xcon:
                print('Cannot connect to XMPP server')
                return False

            auth = cl.auth(jid.getNode(), xmpp_pass, resource=jid.getResource())
            if not auth:
                print('Cannot authenticate to XMPP server')
                return False

            id_ = cl.send(xmpp.protocol.Message(tojid, text))
            print(f'Sent message with id {id_}')

            time.sleep(1)

            cl.disconnect()

        except Exception as e:
           print(f'Exception during "xmpp": {e}, line number: {e.__traceback__.tb_lineno}')
           ok = False

    if not email and not jabber:
        ok = False

    return ok

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, "cmd=summon|descr=Try to get someone's attention")

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
    channel = parts[2] if len(parts) >= 3 else 'nurds'  # default channel if can't be deduced
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'  # default nick if it can't be deduced

    if text[0] != prefix:
        return

    command = text[1:].split(' ')[0]

    if channel in channels:
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'summon':
            try:
                dest = text.split()[1]

                msg  = text

                if summon(dest, msg, nick, channel):
                    client.publish(response_topic, f'{dest} is summoned')

                else:
                    client.publish(response_topic, f'{dest} is not summoned')

            except Exception as e:
                client.publish(response_topic, f'Exception during "summon": {e}, line number: {e.__traceback__.tb_lineno}')

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
