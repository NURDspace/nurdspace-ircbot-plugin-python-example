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


import socket
import sys

mqtt_server  = 'mqtt.vm.nurd.space'   # TODO: hostname of MQTT server
topic_prefix = 'GHBot/'  # leave this as is
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']  # TODO: channels to respond to
prefix       = '!'  # !command, will be updated by ghbot
db           = 'summon.db'
#meshtastic_host = '10.208.43.239'

# summoncfg.py should contain:
#xmpp_user = '...jabber account...'
#xmpp_pass = '...jabber account password...'
#xmpp_host = '...ip-address or hostname of xmpp-server to which xmpp_user belongs...'

con = sqlite3.connect(db)

cur = con.cursor()
cur.execute('PRAGMA journal_mode=wal')
cur.close()


#def send_meshtastic(text):
#    global meshtastic_host
#
#    if meshtastic_host != None:
#        try:
#            import meshtastic
#            import meshtastic.tcp_interface
#
#            iface = meshtastic.tcp_interface.TCPInterface(meshtastic_host)
#
#            iface.sendText(text)
#
#            n_nodes = len(iface.nodes.values()) if iface.nodes else 0
#
#            iface.close()
#
#            return n_nodes
#
#        except Exception as e:
#           print(f'{time.ctime()} Exception during "meshtastic": {e}, line number: {e.__traceback__.tb_lineno}')
#
#    return None
#
#def send_meshtastic_info():
#    global meshtastic_host
#
#    if meshtastic_host != None:
#        try:
#            import meshtastic
#            import meshtastic.tcp_interface
#
#            iface = meshtastic.tcp_interface.TCPInterface(meshtastic_host, debugOut=sys.stdout)
#
#            rc = iface.showInfo()
#
#            iface.close()
#
#            return rc
#
#        except Exception as e:
#           print(f'Exception during "meshtastic": {e}, line number: {e.__traceback__.tb_lineno}')
#
#    return None

def summon(nick, text, by_whom, channel):
    global con
#    global meshtastic_host

    ok = True

#    t = threading.Thread(target=send_meshtastic, args=(text,))
#    t.daemon = True
#    t.start()

    cur = con.cursor()
    cur.execute('SELECT email, jabber FROM entities WHERE nick=?', (nick.lower(),))

    row = cur.fetchone()
    if row == None:
#        if meshtastic_host != None:
#            return (False, 'Summoned via meshtastic')
#
#        else:
            return (False, 'nothing registered for user')

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
           return (False, f'Exception during "sendmail": {e}, line number: {e.__traceback__.tb_lineno}')

    if jabber != None:
        try:
            tojid = jabber

            jid = xmpp.protocol.JID(xmpp_user)
            cl  = xmpp.Client(jid.getDomain(), debug=[])

            #xcon = cl.connect()
            xcon = cl.connect((xmpp_host, 5222))
            if not xcon:
                return (False, 'Cannot connect to XMPP server')

            auth = cl.auth(jid.getNode(), xmpp_pass, resource=jid.getResource())
            if not auth:
                return (False, 'Cannot authenticate to XMPP server')

            id_ = cl.send(xmpp.protocol.Message(tojid, text))
            print(f'Sent message with id {id_}')

            time.sleep(1)

            cl.disconnect()

        except Exception as e:
           return (False, f'Exception during "xmpp": {e}, line number: {e.__traceback__.tb_lineno}')

    if not email and not jabber:
#        if meshtastic_host != None:
#            return (False, 'Summoned via meshtastic')
#
#        else:
            return (False, 'No summon protocol registered for that user')

    return (True, '')

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, "cmd=summon|descr=Try to get someone's attention")
#    client.publish(target_topic, "cmd=meshtastic|descr=Try to get someone's attention via meshtastic")
#    client.publish(target_topic, "cmd=meshinfo|descr=Meshtastic state info")

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

    if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'summon':
            try:
                dest = text.split()[1]

                msg  = f'You were summoned by {nick}: {text}'

                rc   = summon(dest, msg, nick, channel)

                if rc[0]:
                    client.publish(response_topic, f'{dest} is summoned')

                else:
                    client.publish(response_topic, f'{dest} is not summoned: {rc[1]}')

            except Exception as e:
                client.publish(response_topic, f'Exception during "summon": {e}, line number: {e.__traceback__.tb_lineno}')

#        elif command == 'meshtastic':
#            try:
#                only_nick = nick[0:nick.find('!')]
#
#                only_text = text[text.find(' '):].strip()
#
#                msg  = f'{only_nick}: {only_text}'
#
#                n_nodes = send_meshtastic(msg)
#
#                if n_nodes == None:
#                    client.publish(response_topic, 'Fail')
#
#                else:
#                    client.publish(response_topic, f'Sent to aprox. {n_nodes} nodes')
#
#            except Exception as e:
#                client.publish(response_topic, f'Exception during "meshtastic": {e}, line number: {e.__traceback__.tb_lineno}')
#
#        elif command == 'meshinfo':
#            try:
#                print(send_meshtastic_info())
#
#            except Exception as e:
#                client.publish(response_topic, f'Exception during "meshinfo": {e}, line number: {e.__traceback__.tb_lineno}')

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
