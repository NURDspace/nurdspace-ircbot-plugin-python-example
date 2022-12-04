#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import math
import paho.mqtt.client as mqtt
#from py_expression_eval import Parser
import random
import re
import requests
import threading
import time
import urllib.parse


import socket
import sys

mqtt_server  = 'mqtt.vm.nurd.space'
topic_prefix = 'GHBot/'
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']
prefix       = '!'

choices      = []
last_urls    = []


def find_urls(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?]))"

    url = re.findall(regex,string)      

    return [x[0] for x in url]

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
    client.publish(target_topic, 'cmd=regen|descr=Regenvoorspelling voor omgeving Wageningen')
    client.publish(target_topic, 'cmd=@|descr=What is the titel of the last URL posted')
#    client.publish(target_topic, 'cmd=reken|descr=Calculate a simple formula')
    client.publish(target_topic, 'cmd=bmi|descr=Bereken de BMI. Parameter 1: lengte, 2: gewicht.')
    client.publish(target_topic, 'cmd=qanime|descr=Anime quote')
    client.publish(target_topic, 'cmd=dogfact|descr=Dog facts')
    client.publish(target_topic, 'cmd=profanity|descr=Check if a text contains profanity')
    client.publish(target_topic, 'cmd=random|descr=Return a random number')
    client.publish(target_topic, 'cmd=love|descr=Who is a good boy! (m/v/x)')
    client.publish(target_topic, 'cmd=op|descr=Give the requester operator-rights')

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
        r = requests.get('https://bit.rtvrijnstreek.nl/web.html', timeout=10)

        client.publish(response_topic, r.content.decode('utf-8').splitlines()[0])

    except Exception as e:
        client.publish(response_topic, f'Exception during "rijnstreek": {e}, line number: {e.__traceback__.tb_lineno}')

def cmd_janee(client, response_topic):
    client.publish(response_topic, random.choice(['ja', 'nee', 'ja', 'nein']))

def cmd_at(client, response_topic):
    urls = []

    for url in last_urls:
        try:
            r = requests.get(url, timeout=10)

            text = r.content.decode('utf-8')
            textl = text.lower()
        
            title_start = textl.find('<title>')

            if title_start == -1:
                continue

            title_end = textl.find('</title>', title_start)

            if title_end == -1:
                continue

            title = text[title_start + 7:title_end]

            if len(title) > 64:
                title = title[0:61] + '<...>'

            if len(url) > 32:
                url = url[0:30] + '<...>'

            urls.append(f'{url}: {title}')

        except Exception as e:
            print(f'{url} failed: {e}')

    client.publish(response_topic, ', '.join(urls))

def cmd_regen(client, response_topic):
    try:
        r = requests.get('https://gpsgadget.buienradar.nl/data/raintext/?lat=51.97&lon=5.67', timeout=10)
        data = r.content.decode('ascii')

        client.publish(response_topic, r.content.decode('ascii'))

        result = []

        lines = data.split('\n')

        for line in lines:
            if line == '':
                continue

            try:
               line = line.rstrip('\r')
               parts = line.split('|')
               mmtemp = float(str(parts[0]))
               mm = math.pow(10.0, ((mmtemp - 109)/32.0))

               if mm >= 0.001:
                   result.append('%s: %.3fmm/u, ' % (parts[1], mm))

            except Exception as e:
                client.publish(response_topic, f'Exception during "regen": {e}, line number: {e.__traceback__.tb_lineno}')
                break

        if len(result) == 0:
            client.publish(response_topic, f'Geen regen voorspeld door buienradar.nl')

        else:
            client.publish(response_topic, f'Regenvoorspelling van buienradar.nl: {" ".join(result)}')

    except:
        client.publish(response_topic, f'Exception during "regen": {e}, line number: {e.__traceback__.tb_lineno}')

#def cmd_reken(client, response_topic, message):
#    try:
#        parser = Parser()

#        result = parser.parse(message).evaluate({})

#        client.publish(response_topic, f'De uitkomst is: {result}')

#    except Exception as e:
#        client.publish(response_topic, f'Exception during "reken": {e}, line number: {e.__traceback__.tb_lineno}')

def cmd_bmi(client, response_topic, parameters):
    try:
        height = float(parameters[0])
        weight = float(parameters[1])

        oldBMI =       weight / math.pow(height, 2);
        newBMI = 1.3 * weight / math.pow(height, 2.5);

        client.publish(response_topic, f'Old BMI: {oldBMI:.2f}, new BMI: {newBMI:.2f}')

    except Exception as e:
        client.publish(response_topic, f'Exception during "bmi": {e}, line number: {e.__traceback__.tb_lineno}')

def cmd_profanity(client, response_topic, value):
    try:
        if value == '':
            return

        r = requests.get('https://www.purgomalum.com/service/containsprofanity?text=' + urllib.parse.quote(value), timeout=10)

        client.publish(response_topic, f"Profanity: {r.content.decode('ascii')}")

    except Exception as e:
        client.publish(response_topic, f'Exception during "profanity": {e}, line number: {e.__traceback__.tb_lineno}')

def on_message(client, userdata, message):
    global choices
    global last_urls
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

    try:
        if len(parts) > 0 and parts[-1] == 'message':
            new_last_urls = find_urls(text)
            print(new_last_urls)

            # TODO: publish to irc/urls/nurds

            if len(new_last_urls) > 0:
                last_urls = new_last_urls

    except Exception as e:
        print(f'fail: {e} for {text}')

    response_topic = f'{topic_prefix}to/irc/{channel}/notice'
    response_topic_pm = f'{topic_prefix}to/irc/{channel}/privmsg'

    lower_text = text.lower()

    if 'rammstein' in lower_text:
        client.publish(response_topic, 'BUCK DICH')

    if text[0] != prefix:
        return

    parts     = text.split(' ')
    command   = parts[0][1:]
    value     = parts[1]  if len(parts) >= 2 else None
    value_all = parts[1:] if len(parts) >= 2 else None

    # print(channel, nick, command, value)

    if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
        command = text[1:].split(' ')[0]

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
            cmd_allot(client, response_topic, value)

        elif command == 'rijnstreek':
            cmd_rijnstreek(client, response_topic)

        elif command == 'janee':
            cmd_janee(client, response_topic)

        elif command == 'regen':
            cmd_regen(client, response_topic)

        elif command == '@':
            cmd_at(client, response_topic)

#        elif command == 'reken':
#            space = text.find(' ')

#            if space != -1:
#                value = text[space:].strip()

#                cmd_reken(client, response_topic, value)

        elif command == 'bmi' and len(value_all) == 2:
            cmd_bmi(client, response_topic, value_all)

        elif command == 'qanime':
            try:
                j = get_json('https://animechan.vercel.app/api/random')

                quote = f'{j["quote"]} ({j["anime"]} / {j["character"]})'

                client.publish(response_topic, quote)

            except Exception as e:
                client.publish(response_topic, f'Exception during "qanime": {e}, line number: {e.__traceback__.tb_lineno}')

        elif command == 'dogfact':
            try:
                j = get_json('https://dog-api.kinduff.com/api/facts')

                fact = j['facts'][0]

                client.publish(response_topic, fact)

            except Exception as e:
                client.publish(response_topic, f'Exception during "dogfact": {e}, line number: {e.__traceback__.tb_lineno}')

        elif command == 'profanity':
            space = text.find(' ')

            if space != -1:
                value = text[space:].strip()

                cmd_profanity(client, response_topic, value)

        elif command == 'random':
            r = random.randint(0, int(value)) if value != None else int(random.random() * 10)

            client.publish(response_topic, f'A random number is {r}')

        elif command == 'love':
            client.publish(response_topic_pm, f'%m loves you all')

        elif command == 'op':
            if '!' in nick:
                nick = nick[0:nick.find('!')]

            client.publish(f'{topic_prefix}to/irc/{channel}/mode', f'+o {nick}')

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
