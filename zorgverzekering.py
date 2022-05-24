#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import random
import requests
import threading
import time
import urllib.parse


mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'test', 'nurdsbofh']
prefix       = '!'

choices      = []


def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    client.publish(target_topic, 'cmd=zorgverzekering|descr=Hulp bij de keuze van een zorgverzekering.')
    client.publish(target_topic, 'cmd=test|descr=Werkt deze dingetje?')
    client.publish(target_topic, 'cmd=quit|descr=Afsluiten')
    client.publish(target_topic, 'cmd=choose|descr=Choose between comma seperated choices.')
    client.publish(target_topic, 'cmd=secondopinion|descr=Eh...')
    client.publish(target_topic, 'cmd=spacehex|descr=Show current color of the space.')
    client.publish(target_topic, 'cmd=wau-temp|descr=Temperature etc. in Wageningen.')
    client.publish(target_topic, 'cmd=allot|descr=Show allotments for a given day')
    client.publish(target_topic, 'cmd=rijnstreek|descr=Rijnstreek FM currently playing')
    client.publish(target_topic, 'cmd=janee|descr=Voor levensvragen')

def parse_to_rgb(json):
    if "value" in json:
        return int(round((json['value'] / 100) * 255))


def get_json(url):
    r = requests.get(url)

    return r.json()

def get_rgb():
    return [parse_to_rgb(
                get_json("http://lichtsensor.dhcp.nurd.space/sensor/tcs34725_" + channel + "_channel"))
                for channel in ["red", "green", "blue"]]

def cmd_wau_temp(client, response_topic):
    try:
        r = requests.get('http://met.wur.nl/veenkampen/data/C_current.txt', timeout=10)

        thermopage = r.content.decode('ascii').split()

        currentline = thermopage[-1]

        data = currentline.split(',')

#        temp = str(round(float(data[2]),1))
        temp = data[2]
        humid = str(round(float(data[8]),1))
        sunshine = data[9]
        visibility = data[18]
        precip = data[19]
        pressure = str(float(data[21]))
#        windspeed = str(round(float(data[22]),1))
        windspeed = float(data[22])
        windspeedstring = str(round(float(data[22]),1))
        windangle = float(data[26])+11.25
        winddir = ''

        if windangle>0 and windangle<= 22.5: winddir = 'N'
        if windangle>22.5 and windangle<= 45: winddir = 'NNE'
        if windangle>45 and windangle<= 67.5: winddir = 'NE'
        if windangle>67.5 and windangle<= 90: winddir = 'ENE'
        if windangle>90 and windangle<= 112.5: winddir = 'E'
        if windangle>112.5 and windangle<= 135: winddir = 'ESE'
        if windangle>135 and windangle<= 157.5: winddir = 'SE'
        if windangle>157.5 and windangle<= 180: winddir = 'SSE'
        if windangle>180 and windangle<= 202.5: winddir = 'S'
        if windangle>202.5 and windangle<= 225: winddir = 'SSW'
        if windangle>225 and windangle<= 247.5: winddir = 'SW'
        if windangle>247.5 and windangle<= 270: winddir = 'WSW'
        if windangle>270 and windangle<= 292.5: winddir = 'W'
        if windangle>292.5 and windangle<= 315: winddir = 'WNW'
        if windangle>315 and windangle<= 337.5: winddir = 'NW'
        if windangle>337.5 and windangle<= 360: winddir = 'NNW'
        if windangle>360 and windangle<= 382.5: winddir = 'N'

        if windspeed>0 and windspeed<= 0.3: windbeaufort = '0'
        if windspeed>0.3 and windspeed<= 1.5: windbeaufort = '1'
        if windspeed>1.5 and windspeed<= 3.3: windbeaufort = '2'
        if windspeed>3.3 and windspeed<= 5.5: windbeaufort = '3'
        if windspeed>5.5 and windspeed<= 7.9: windbeaufort = '4'
        if windspeed>7.9 and windspeed<= 10.7: windbeaufort = '5'
        if windspeed>10.7 and windspeed<= 13.8: windbeaufort = '6'
        if windspeed>13.8 and windspeed<= 17.1: windbeaufort = '7'
        if windspeed>17.1 and windspeed<= 20.7: windbeaufort = '8'
        if windspeed>20.7 and windspeed<= 24.4: windbeaufort = '9'
        if windspeed>24.4 and windspeed<= 28.4: windbeaufort = '10'
        if windspeed>28.4 and windspeed<= 32.6: windbeaufort = '11'
        if windspeed>32.6: windbeaufort = '12'

        client.publish(response_topic, temp+' C, '+sunshine+' W/m2 sun, '+humid+'% humidity, '+windbeaufort+' bft ('+windspeedstring+' m/s) '+winddir+', '+precip+' mm precipitation, '+pressure+' kPa.')

    except Exception as e:
        client.publish(response_topic, f'Exception during "wau-temp": {e}, line number: {e.__traceback__.tb_lineno}')

def cmd_allot(client, response_topic, value):
    try:
        value = '' if value == None else value.lower()

        r = requests.get('https://portal.nurdspace.nl/nurdallot/public/reportallotniz.php?day=' + urllib.parse.quote(value[0:25]), timeout=10)

        client.publish(response_topic, r.content.decode('ascii'))

    except Exception as e:
        client.publish(response_topic, f'Exception during "allot": {e}, line number: {e.__traceback__.tb_lineno}')

def cmd_rijnstreek(client, response_topic):
    try:
        r = requests.get('https://bit.rtvrijnstreek.nl/web.html')

        client.publish(response_topic, r.content.decode('utf-8').splitlines()[0])

    except Exception as e:
        client.publish(response_topic, f'Exception during "rijnstreek": {e}, line number: {e.__traceback__.tb_lineno}')

def cmd_janee(client, response_topic):
    client.publish(response_topic, random.choice(['ja', 'nee', 'ja', 'nein']))

def on_message(client, userdata, message):
    global choices
    global prefix

    text = message.payload.decode('utf-8')

    topic = message.topic[len(topic_prefix):]

    if topic == 'from/bot/command' and text == 'register':
        announce_commands(client)

        return

    if topic == 'from/bot/parameter/prefix':
        prefix = text

        return

    if text[0] != prefix:
        return

    parts   = topic.split('/')
    channel = parts[2] if len(parts) >= 3 else 'nurds'
    nick    = parts[3] if len(parts) >= 4 else 'jemoeder'

    parts     = text.split(' ')
    command   = parts[0][1:]
    value     = parts[1]  if len(parts) >= 2 else None
    value_all = parts[1:] if len(parts) >= 2 else None

    print(channel, nick, command, value)

    if channel in channels:
        command = text[1:].split(' ')[0]

        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        if command == 'zorgverzekering':
            client.publish(response_topic, 'Het beste neem je een zorgverzekering die je ziektekosten afdekt.')

        elif command == 'test':
            client.publish(response_topic, 'Deze dingetje werks.')

        elif command == 'quit':
            client.publish(response_topic, 'NOOID!')

        elif command == 'choose':
            choices = ' '.join(text.split(' ')[1:]).split(',')

            client.publish(response_topic, random.choice(choices).strip())

        elif command == 'secondopinion':
            if len(choices) == 0:
                client.publish(response_topic, 'Nothing to choose from')

            else:
                client.publish(response_topic, random.choice(choices).strip())

        elif command == 'spacehex':
            hexcolor = "#{:02x}{:02x}{:02x}".format(*get_rgb())

            client.publish(response_topic, 'Current hex color of zaal 1 is: ' + hexcolor)

        elif command == 'wau-temp':
            cmd_wau_temp(client, response_topic)

        elif command == 'allot':
            print(client, response_topic, value)
            cmd_allot(client, response_topic, value)

        elif command == 'rijnstreek':
            cmd_rijnstreek(client, response_topic)

        elif command == 'janee':
            cmd_janee(client, response_topic)

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
