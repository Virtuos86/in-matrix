#qpy:kivy
# coding: utf-8

'''
'''

def platform(predicate, true, false):
    if kivy.platform() == predicate:
        return true
    else:
        return false

APP_TITLE = u"Neo"
COLORS = (
    (.75, .75, .75, 1), # 'silver'
    (0, 0, 1, 1), #       'blue'
    (0.5, 0.5, 0.5, 1), # 'gray'
    (0, 0.5, 0, 1), #     'green'
    (0, 1, 0, 1), #       'lime'
    (0.5, 0, 0, 1), #     'maroon'
    (0, 0, 0.5, 1), #     'navy'
    (0.5, 0, 0.5, 1), #   'purple'
    (1, 0, 0, 1), #       'red'
    (0, 0.5, 0.5, 1), #   'teal'
)
COMMANDS = [
    '/nick',  #  <display_name>: change your display name
    '/me',    #  <action>: send the action you are doing. /me will be replaced by your display name
    '/join',  #  <room_alias>: join a room
    '/leave', #  <user_id>: leave current room
    '/kick',  #  <user_id> [<reason>]: kick the user
    '/ban',   #  <user_id> [<reason>]: ban the user
    '/unban', #  <user_id>: unban the user
    '/op',    #  <user_id> <power_level>: set user power level
    '/deop',  #  <user_id>: reset user power level to the room default value
]
FONTS = {
    'timeline': './res/fonts/FreeMonoBoldOblique.ttf',
    'notifications': './res/fonts/RobotoCondensed-Bold.ttf',
    'post-buffer': './res/fonts/DroidSans.ttf',
}


def gen_index():
    i = 0
    while True:
        yield i
        i += 1
_gen_index = gen_index()

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')
#sys.stdout = sys.stderr = open('log.txt', 'w')
from random import choice
import pprint
import codecs
import json
import datetime
import kivy

if platform('android', True, False):
    kivy.require('1.0.8')
else:
    kivy.require('1.8.0')

from kivy.core.window import Window
Window.clearcolor = (1, 1, 1, 1)
Window.set_title(APP_TITLE)
Window.set_icon('./res/img/icon.png')

from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.slider import Slider
from kivy.uix.screenmanager import WipeTransition
from kivy.uix.screenmanager import  FadeTransition
from kivy.uix.screenmanager import NoTransition
from kivy.uix.popup import Popup
from kivy.config import Config
from kivy.base import runTouchApp
from kivy.app import App
from kivy.lang import Builder

import net

def load_settings():
    with open('settings.json') as f:
        s = json.load(f)
        user_id = s["user_id"]
        try:
            password = s["password"].decode('base64')
        except:
            password = s["password"]
        default_room_alias = s["default_room_alias"]
        server = s["server"]
    return user_id, password, default_room_alias, server

def update_timeline(timeline, contents=None):
    if contents is None:
        pass #timeline.add_widget(Label(text="[b]Nothing[/b]", markup=True, size_hint_y=None, height=20))
    else:
        msg = TextInput(text=contents,
            size_hint_y=None,
            font_name=FONTS['timeline'],
            readonly=True,
        )
        msg.background_color = choice(COLORS)
        msg.foreground_color = [0, 0, 0, 1]
        k = len(contents.splitlines())
        msg.size = (Window.width, msg.line_height * (k if k > 1 else 2))
        timeline.add_widget(msg)

def exec_cmd(cmd, data):
    resp = ''
    if cmd == '/nick':
        pass
    elif cmd == '/me':
        resp = app.current_room.send_text(app.user_id + ' ' + data)
    elif cmd == '/join':
        resp = app.client.join_room(data)
    elif cmd == '/leave':
        resp = app.current_room.leave(None)
    elif cmd == '/kick':
        user_id, reason = (data + ' ').split(' ', 1)[:2]
        resp = app.current_room.kick_user(user_id, reason)
    elif cmd == '/ban':
        user_id, reason = (data + ' ').split(' ', 1)[:2]
        resp = app.current_room.ban_user(user_id, reason)
    elif cmd == '/unban':
        pass
    elif cmd == '/op':
        pass
    elif cmd == '/deop':
        pass
    return resp

def parse_membership(event):
    pass

def parse_msg(event):
    e = event
    body = e["content"]["body"]
    if u'body' in e[u'content']:
        update_timeline(app.window.timeline, '[%s~%s]\n%s: %s' % (e[u'age'], datetime.datetime.fromtimestamp(int(e["origin_server_ts"] / 1000)).strftime('%Y-%m-%d %H:%M:%S'), e[u'user_id'], e[u'content'][u'body']))
    if (e["user_id"] == app.user_id or e["content"]["msgtype"] == "m.notice"):
        return    

def room_callback(event):
    open('log_room', 'a').write(pprint.pformat(event) + '\n\n\n')
    e = event
    if u'body' in e[u'content']:
        update_timeline(app.window.timeline, '[%s~%s]\n%s: %s' % (e[u'age'], datetime.datetime.fromtimestamp(int(e["origin_server_ts"] / 1000)).strftime('%Y-%m-%d %H:%M:%S'), e[u'user_id'], e[u'content'][u'body']))

def user_callback(event):
    open('log_user', 'a').write(pprint.pformat(event) + '\n\n\n')
    e = event
    etype = e["type"]
    switch = {
        "m.room.member": parse_membership,
        "m.room.message": parse_msg,
        "m.room.message.feedback": lambda event: None,
        "m.room.topic": lambda event: None,
        "m.room.name": lambda event: None,
        "m.room.invite": lambda event: None,
        "m.room.join": lambda event: None,
        "m.room.leave": lambda event: None,
        "m.room.ban": lambda event: None,
    }
    try:
        switch[etype](event)
    except KeyError:
        pass
    if "room_id" in e:
        app.client.rooms["room_id"] = e["room_id"]
    if etype == u'm.presence':
        if u'displayname' in e[u'content']:
            user_id, user_ids = e[u'content'][u'displayname'], app.current_room.user_ids
            if user_id not in user_ids:
                user_ids.append(user_id)


class Room(Screen):
    """
    """
    def __init__(self, **kwa):
        super(Room, self).__init__(**kwa)
        self.root = root = GridLayout(cols=1, rows=5)
        self.title = Label(text=self.name,
            bold=True,
            color=[0, 0, 0, 1],
            markup=True,
            size_hint=(1, platform('linux', 0.05, 0.1))
        )
        root.add_widget(self.title)
        self.mline = TextInput(text="%s" % self.name,
            multiline=False,
            size_hint=(1, platform('linux', 0.06, 0.1)),
            foreground_color=[0.2, 0.4, 0.2, 1],
            background_color=[1, 1, 1, 0.5],
            font_name=FONTS['notifications']
        )
        root.add_widget(self.mline)
        self.body = ScrollView(size_hint=(1, 0.8))
        self.timeline = timeline = GridLayout(cols=1, spacing=1, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        timeline.bind(minimum_height=timeline.setter('height'))
        update_timeline(timeline)
        self.body.add_widget(timeline)
        root.add_widget(self.body)
        self.postbuf = postbuf = GridLayout(cols=1, rows=3, spacing=1, size_hint=(1, platform('linux', 0.3, 0.5)))
        self.textbuf = textbuf = TextBuffer(text=u'', size_hint=(1, 0.9))
        postbuf.add_widget(textbuf)
        self.empty = empty = Label(size_hint_y=0)
        root.add_widget(postbuf)
        root.add_widget(empty)
        self.add_widget(root)

    def notify(self, message):
        app.window.mline.text = message

#
class TextBuffer(TextInput):
    """
    """
    def __init__(self, **kwa):
        super(TextBuffer, self).__init__(**kwa)
        self.hint_text = u'Type here! Press <Ctrl><Enter> to send a message.'
        self.pos_hint = {'top': True}
        self.size_hint = (1, platform('linux', 0.2, 0.3))
        #self.auto_indent = True
        self.border = (10, 50, 50, 50)
        self.font_size = 20
        self.font_name = FONTS['post-buffer']
        self.background_color = [0.8, 0.8, 0.8, 0.8]
        self.foreground_color = [0.1, 0.1, 0.1, 1]
        self.cursor_color = [1, 1, 0, 1]
        self.bind(focus=self._focus)

    def _focus(self, instance, v
        if platform('android', True, False):
            if value:
                app.window.empty.size_hint_y = 0.9 #Window.width, Window.keyboard_height
            else:
                app.window.empty.size_hint_y = 0

    def autocomplete(self):
        line = self._lines[self.cursor_row]
        col = self.cursor_col
        pos = line.rfind(' ', 0, col)
        word = line[(0 if pos <= 0 else pos + 1):col]
        variants = []
        for user_id in app.current_room.user_ids:
            if user_id.startswith(word):
                variants.append(user_id)
        else:
            if len(variants) == 1:
                for i in word:
                    self.do_backspace()
                else:
                    self.insert_text(variants[0] + ' ')

    def insert_text(self, substring, from_undo=False, len=len):
        std_ins = TextInput.insert_text
        if len(substring) == 1:
            line = self._lines[self.cursor_row]
            if substring ==  u'\n':
                
                # Try find commands:
                if line.split(' ', 1)[0] in COMMANDS:
                    try:
                        resp = exec_cmd(*(line + ' ').split(' ', 1)[:2])
                    except Exception, e:
                            app.window.notify(str(e))
                    else:
                        if isinstance(resp, dict):
                            app.window.notify(resp[u'event_id'])
                    self.text = ''
                else:
                    try:
                        row = self.cursor_row
                        if row > 0:
                            line = self._lines[row]
                            if line ==  u'':
                                try:
                                    # if message is not empty
                                    if self.text:
                                        resp = app.current_room.send_text(self.text[:-1])
                                        self.text = ''
                                        if isinstance(resp, dict):
                                            app.window.notify(resp[u'event_id'])
                                    else:
                                        std_ins(self, substring, from_undo)
                                except net.API.MatrixRequestError, e:
                                    app.window.notify(e)
                                except AttributeError:
                                    pass
                            else:
                                std_ins(self, substring, from_undo)
                        else:
                            std_ins(self, substring, from_undo)
                    except NameError, e: print e
            else:
                std_ins(self, substring, from_undo)
        else:
            std_ins(self, substring, from_undo)

#
class MatrixApp(App):
    """
    """
    def __init__(self):
        pass

    def build(self):
        root = ScreenManager(transition=NoTransition())
        root.fullscreen = True
        root.orientation = "auto"
        
        root.user_id, root.password, root.current_room_alias, root.server = load_settings()
        room = Room(name=root.current_room_alias)
        root.add_widget(room)
        try:
            root.client, root.access_token = net.sign_in_matrix(root.server, root.user_id, root.password)
            root.current_room = root.client.join_room(root.current_room_alias)
            root.current_room.add_listener(room_callback)
            root.current_room.user_ids = []
            root.client.add_listener(user_callback)
            root.client.start_listener_thread()
            root.client._sync()
        except net.API.MatrixRequestError:
            pass
        root.window = root.current_screen
        return root

    def on_pause(self):
        return True

    def on_resume(self):
        return True


def global_keyboard_callback(key, scancode, codepoint, modifiers):
    #print 'key:', key, 'scancode:', scancode, 'codepoint:', repr(codepoint), 'modifiers:', modifiers
    if modifiers:
        if 'ctrl' in modifiers:

            # <Ctrl><Tab>: autocomplete
            if key == 9:
                if app.window.textbuf:
                    app.window.textbuf.autocomplete()

            # <Ctrl><Backspace>: backspace word
            if key == 8:
                if app.window.textbuf:
                    textbuf = app.window.textbuf
                    separators = ' ,.:;<>\'"([{}])'
                    col = textbuf.cursor_col
                    line = textbuf._lines[textbuf.cursor_row]
                    pos = max(line.rfind(s, 0, col) for s in separators) + 1
                    for i in line[pos:col]: textbuf.do_backspace()

            # <Ctrl><Enter>: send message
            elif key == 13:
                if app.window.textbuf:
                    try:
                        textbuf = app.window.textbuf
                        resp = app.current_room.send_text(textbuf.text[:-1])
                        textbuf.text = ''
                        if isinstance(resp, dict):
                            app.window.notify(resp[u'event_id'])
                    except net.API.MatrixRequestError, e:
                        app.window.notify(str(e))
                    except AttributeError:
                        pass

            # <Ctrl><0-9>: switch to room <№>
            elif key in (48,49,50,51,52,53,54,55,56,57):
                app.current = app.screens[min(key, len(app.screens) - 1)].name

            # <Ctrl><n>: create new window for joining new room
            elif key == 110:
                app.add_widget(Room(name=str(_gen_index.next())))

            # <Ctrl><`<`>: switch to previous room
            elif key == 276:
                app.current = app.previous()

            # <Ctrl><`>`>: switch to next room
            elif key == 275:
                app.current = app.next()
    #return True
Window.on_keyboard = global_keyboard_callback

##########################
if __name__ == '__main__':
    app = MatrixApp().build()
    runTouchApp(app)
