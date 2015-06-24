from time import sleep
from kivy.clock import Clock
from kivy.lib import osc


serviceport = 3000
activityport = 3001

def callback(message, *args):
    answer_message(message[2:])

def answer_message(message):
    osc.sendMsg('/im', message, port=activityport)

def check_new_mention():
    msg = ["+"]
    msg.append("")
    answer_message(msg)


if __name__ == '__main__':
    osc.init()
    oscid = osc.listen(ipAddr='127.0.0.1', port=serviceport)
    osc.bind(oscid, callback, '/im')
    Clock.schedule_interval(lambda *x: check_new_mention(), 10)

    while True:
        osc.readQueue(oscid)
        sleep(1)
