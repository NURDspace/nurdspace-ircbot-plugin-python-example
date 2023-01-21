#! /usr/bin/python3

# by FvH, released under Apache License v2.0

# either install 'python3-paho-mqtt' or 'pip3 install paho-mqtt'

import paho.mqtt.client as mqtt
import threading
import time
import random
import sys

mqtt_server  = 'mqtt.vm.nurd.space'   # TODO: hostname of MQTT server
topic_prefix = 'GHBot/'  # leave this as is
channels     = ['nurdbottest', 'nurds', 'nurdsbofh']  # TODO: channels to respond to
prefix       = '!'  # !command, will be updated by ghbot

distri = [
    "AlmaLinux",
    "Asianux",
    "ClearOS",
    "Fermi",
    "Miracle Linux",
    "Oracle Linux",
    "Red Flag Linux",
    "Rocks Cluster Distribution",
    "Rocky Linux",
    "Scientific Linux",
    "Amazon Linux",
    "Berry Linux",
    "BLAG Linux and GNU",
    "CentOS Stream",
    "EnGarde Secure Linux",
    "Fuduntu",
    "Hanthana",
    "Korora",
    "Linpus Linux",
    "Linux XP",
    "MeeGo",
    "Moblin",
    "Network Security Toolkit",
    "Qubes OS",
    "Red Star OS",
    "Russian Fedora Remix",
    "Sugar-on-a-Stick Linux",
    "Trustix",
    "Yellow Dog Linux",
    "GeckoLinux",
    "SUSE Linux Enterprise",
    "Mageia",
    "ROSA Linux",
    "OpenMandriva",
    "ALT Linux",
    "Caldera OpenLinux",
    "PCLinuxOS",
    "Red Hat Linux",
    "SUSE Linux",
    "Think Blue Linux",
    "Turbolinux",
    "Vine Linux",
    "Lubuntu",
    "Ubuntu Budgie",
    "Ubuntu Kylin",
    "Ubuntu MATE",
    "Ubuntu Server",
    "Ubuntu Studio",
    "Xubuntu",
    "Edubuntu",
    "Gobuntu",
    "Mythbuntu",
    "Ubuntu for Android",
    "Ubuntu GNOME",
    "Ubuntu JeOS",
    "Ubuntu Mobile",
    "Ubuntu Netbook Edition",
    "Ubuntu Touch",
    "Ubuntu TV",
    "BackBox",
    "BackSlash",
    "Bodhi Linux",
    "Cub Linux",
    "dyne:bolic",
    "EasyPeasy",
    "Eeebuntu",
    "Element OS",
    "elementary OS",
    "Emmabuntü",
    "GalliumOS",
    "GendBuntu",
    "Goobuntu",
    "gOS",
    "Joli OS",
    "Karoshi",
    "KDE neon",
    "LiMux",
    "Linux Lite",
    "Linux Mint",
    "LinuxMCE",
    "LinuxTLE",
    "LliureX	",
    "LXLE",
    "MAX",
    "Molinux",
    "Netrunner",
    "Nova",
    "OpenGEU",
    "Peppermint OS",
    "Pinguy OS",
    "Pop! OS",
    "Poseidon Linux",
    "Sabily",
    "SuperGamer",
    "Trisquel GNU/Linux",
    "UberStudent",
    "Ubuntu Unity",
    "Ututo",
    "Vinux",
    "Zorin OS",
    "Damn Small Linux",
    "Feather Linux",
    "antiX",
    "Astra Linux",
    "BackTrack",
    "Bharat Operating System Solutions (BOSS)",
    "Canaima",
    "Corel Linux",
    "CrunchBang Linux",
    "Deepin",
    "Devuan",
    "DoudouLinux",
    "Dreamlinux",
    "Emdebian Grip",
    "Finnix",
    "gLinux",
    "gNewSense",
    "grml",
    "HandyLinux",
    "Kali Linux",
    "Kanotix",
    "Kurumin",
    "LEAF Project",
    "Libranet",
    "LiMux",
    "LMDE",
    "Maemo",
    "MEPIS",
    "MintPPC",
    "Musix GNU+Linux",
    "MX Linux",
    "NepaLinux",
    "OpenZaurus",
    "Pardus",
    "Parrot OS",
    "Parsix",
    "PelicanHPC",
    "PureOS",
    "Q4OS",
    "Raspberry Pi OS",
    "Sacix",
    "Skolelinux",
    "SolydXK",
    "SparkyLinux",
    "Sunwah Linux",
    "The Amnesic Incognito Live System (TAILS)",
    "TurnKey Linux",
    "Twister OS",
    "Univention Corporate Server",
    "Webconverger",
    "Vyatta",
    "VyOS",
    "Antergos",
    "ArchBang",
    "Artix Linux",
    "ArchLabs",
    "Asahi Linux",
    "BlackArch",
    "EndeavourOS",
    "Garuda Linux",
    "Hyperbola GNU/Linux-libre",
    "LinHES",
    "Manjaro",
    "Parabola GNU/Linux-libre",
    "SteamOS",
    "SystemRescue",
    "Chakra Linux",
    "Frugalware Linux",
    "Calculate Linux",
    "ChromeOS",
    "Chromium OS",
    "Clip OS",
    "Container Linux",
    "Pentoo",
    "Sabayon Linux",
    "Ututo",
    "Absolute Linux",
    "Austrumi Linux",
    "Damn Vulnerable Linux",
    "KateOS",
    "MuLinux",
    "NimbleX",
    "Platypux",
    "Porteus",
    "Salix OS",
    "Sentry Firewall",
    "Slackintosh",
    "Slax",
    "Topologilinux",
    "VectorLinux",
    "Zenwalk",
    "ZipSlack",
    "/e/",
    "Android-x86",
    "CalyxOS",
    "CopperheadOS",
    "CyanogenMod",
    "DivestOS",
    "Fire OS",
    "GrapheneOS",
    "HarmonyOS",
    "LineageOS",
    "OmniROM",
    "Paranoid Android",
    "Remix OS",
    "Replicant",
    "Resurrection Remix OS",
    "CRUX",
    "Linux From Scratch",
    "GNU Guix System",
    "GoboLinux",
    "NixOS",
    "Sorcerer",
    "Source Mage",
    "T2 SDE",
    "4MLinux",
    "Alpine Linux",
    "Billix",
    "CHAOS",
    "Clear Linux OS",
    "DD-WRT",
    "Dragora GNU/Linux-Libre",
    "ELinOS",
    "Firefox OS",
    "fli4l",
    "Foresight Linux",
    "GeeXboX",
    "Jlime",
    "KaiOS",
    "KaOS",
    "Kwort",
    "Lightweight Portable Security (LPS)",
    "Linux for PlayStation 2",
    "Linux Router Project",
    "MeeGo",
    "MkLinux",
    "Nitix",
    "MontaVista Linux",
    "OpenWrt",
    "postmarketOS",
    "Prevas Industrial Linux",
    "Puppy Linux",
    "rPath",
    "SliTaz",
    "Smallfoot",
    "SmoothWall",
    "paldo",
    "Sailfish OS",
    "Solus",
    "Tinfoil Hat Linux",
    "Tiny Core Linux",
    "Tizen",
    "tomsrtbt",
    "Void Linux",
    "MCC Interim Linux",
    "Softlanding Linux System",
    "Yggdrasil Linux/GNU/X",
    "Nobara"
]

def announce_commands(client):
    target_topic = f'{topic_prefix}to/bot/register'

    # TODO: one or more of these:
    client.publish(target_topic, 'cmd=distro|descr=Helpt je om een geschikte distro te kiezen')
    # you can add |agrp=groupname

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

    tokens = text[1:].split(' ')

    if len(tokens) == 2:
        command = tokens[0]
        recipient = tokens[1]
        sender = nick.split('!')[0]
        give_distro_to_someone = True
    else:
        command = tokens[0]
        recipient = nick.split('!')[0]
        give_distro_to_someone = False

    if channel in channels or (len(channel) >= 1 and channel[0] == '\\'):
        response_topic = f'{topic_prefix}to/irc/{channel}/privmsg'

        # TODO: implementation of each command
        if command == 'distro':
            distro = random.choice(distri)
            if give_distro_to_someone:
                client.publish(response_topic, 'Hey {0}, je wil {1} draaien!'.format(recipient, distro))
            else:
                client.publish(response_topic, '{0}'.format(distro))

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

client = mqtt.Client(sys.argv[0], clean_session=False)
client.on_message = on_message
client.on_connect = on_connect
client.connect(mqtt_server, port=1883, keepalive=4, bind_address="")

t = threading.Thread(target=announce_thread, args=(client,))
t.start()

client.loop_forever()
