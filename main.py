#qpy:kivy
# coding: utf-8

'''
'''

def platform(predicate, true, false):
    if kivy.platform() == predicate:
        return true
    else:
        return false

APP_TITLE = u"In-Matrix (IM)"
PATH_TO_HISTORY = u'./history'
COLORS = (
    (0, 0, 1, 1),       #  'blue'
    (0.5, 0.5, 0.5, 1), #  'gray'
    (0, 0.5, 0, 1),     #  'green'
    (0, 1, 0, 1),       #  'lime'
    (0.5, 0, 0, 1),     #  'maroon'
    (0, 0, 0.5, 1),     #  'navy'
    (0.5, 0, 0.5, 1),   #  'purple'
    (1, 0, 0, 1),       #  'red'
    (.75, .75, .75, 1), #  'silver'
    (0, 0.5, 0.5, 1),   #  'teal'
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
    'timeline'     :  './res/fonts/FreeMonoBoldOblique.ttf',
    'infobar'      :  './res/fonts/RobotoCondensed-Bold.ttf',
    'post-buffer'  :  './res/fonts/DroidSans.ttf',
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
import gzip
import json
import datetime
import os
import kivy
from kivy.core.window import Window

# Window.keyboard_height added in 1.9
if platform('android', True, False):
    if int(kivy.__version__.split('.')[1]) > 8:
        kivy.require('1.9.0')
    else:
        kivy.require('1.8.0')
        Window.keyboard_height = Window.height / 2
else:
    kivy.require('1.8.0')

Window.clearcolor = (0.9, 1, 1, 1)
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
from kivy.uix.screenmanager import WipeTransition, FadeTransition, NoTransition, \
                                   FallOutTransition, SwapTransition, SlideTransition, \
                                   RiseInTransition
from kivy.uix.popup import Popup
from kivy.config import Config
from kivy.base import runTouchApp
from kivy.app import App
from kivy.lang import Builder

import net

##########################################

def load_settings():
    with open('settings.json') as f:
        s = json.load(f)
        user_id = s["user_id"]
        try:
            password = s["password"].decode('base64')
        except:
            password = s["password"]
        default_room_alias = s["default_room_alias"]
        predefined_rooms = s["predefined_rooms"]
        server = s["server"]
    return user_id, password, default_room_alias, server, predefined_rooms

def load_history(room_id):
    path = os.path.join(PATH_TO_HISTORY, room_id, 'allhistory')
    if not os.path.exists(path):
        os.makedirs(os.path.join(PATH_TO_HISTORY, room_id))
        return u''
    with gzip.open(path, 'rb') as hfile:
        return hfile.read().decode('utf-8')

def store_history(room_id, content):
    path = os.path.join(PATH_TO_HISTORY, room_id, 'allhistory')
    if not os.path.exists(path):
        os.makedirs(os.path.join(PATH_TO_HISTORY, room_id))
    with gzip.open(path, 'ab') as hfile:
        hfile.write(content.encode('utf-8'))

def update_timeline(timeline, contents=None):
    if contents is None:
        pass #timeline.add_widget(Label(text="[b]Nothing[/b]", markup=True, size_hint_y=None, height=20))
    else:
        msg = TextInput(text=contents,
            size_hint_y=None,
            font_name=FONTS['timeline'],
            #readonly=True,
        )
        msg.background_color = choice(COLORS)
        msg.foreground_color = [0, 0, 0, 1]
        
        # TODO >_<
        msg.size = (Window.width, (msg.line_height + msg.line_spacing) * len(contents.splitlines()) + msg.padding[1] + msg.padding[3])
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
    # TODO
    pass

def parse_msg(event):
    e = event
    body = e["content"]["body"]
    if u'body' in e[u'content']:
        update_timeline(app.window.timeline, '[>%s<>%s<]\n%s: %s' % (
            e[u'age'],
            datetime.datetime.fromtimestamp(int(e["origin_server_ts"] / 1000)).strftime('%Y-%m-%d %H:%M:%S'),
            e[u'user_id'],
            e[u'content'][u'body'])
        )
    if (e["user_id"] == app.user_id or e["content"]["msgtype"] == "m.notice"):
        return    

def room_callback(event):
    open('common_log', 'w').write(pprint.pformat(event) + '\n\n\n')
    e = event
    etype = e["type"]
    switch = {
        "m.room.member"          : parse_membership,
        "m.room.message"         : parse_msg,
        "m.room.message.feedback": lambda event: None,
        "m.room.topic"           : parse_msg,
        "m.room.name"            : parse_msg,
        "m.room.invite"          : parse_msg,
        "m.room.join"            : parse_msg,
        "m.room.leave"           : parse_msg,
        "m.room.ban"             : parse_msg,
    }
    try:
        switch[etype](event)
    except KeyError:
        pass
    if etype == u'm.presence':
        if u'displayname' in e[u'content']:
            user_id, user_ids = e[u'content'][u'displayname'], app.current_room.user_ids
            if user_id not in user_ids:
                user_ids.append(user_id)

# TODO
user_callback = room_callback

###################
class Room(Screen):
    """
    """
    def __init__(self, **kwa):
        super(Room, self).__init__(**kwa)
        self.root = root = GridLayout(cols=1, rows=5)
        self.title = Label(
            text=self.name,
            bold=True,
            color=[0, 0, 0, 1],
            markup=True,
            size_hint=(1, platform('linux', 0.05, 0.1)),
        )
        root.add_widget(self.title)
        self.infobar = TextInput(
            text="%s" % self.name,
            multiline=False,
            size_hint=(1, platform('linux', 0.06, 0.1)),
            foreground_color=[0.2, 0.4, 0.2, 1],
            background_color=[0.8, 0.8, 0, 0.5],
            font_name=FONTS['infobar']
        )
        root.add_widget(self.infobar)
        self.body = body = GridLayout(cols=2, rows=1)
        body.spacing = 5, 0
        self.left_pane = left_pane = ScrollView(size_hint_x=0.9)
        self.timeline = timeline = GridLayout(
            cols=1,
            spacing=1,
            size_hint_y=None,
        )
        # Make sure the height is such that there is something to scroll.
        timeline.bind(minimum_height=timeline.setter('height'))
        #update_timeline(timeline)
        left_pane.add_widget(timeline)
        self.right_pane = right_pane = GridLayout(cols=1, rows=2, size_hint_x=0.1)
        right_pane.spacing = 0, 5
        rt_body = ScrollView(size_hint=(1, 0.5))
        self.members_list = members_list = GridLayout(
            cols=1,
            spacing=1,
            size_hint_y=None,
            #size=rt_body.size[1]/2,
        )
        members_list.bind(minimum_height=members_list.setter('height'))
        #test item
        mbr_item = TextInput(text="Nothing", size_hint_y=None, height=20, background_color=choice(COLORS), readonly=True)
        mbr_item.size = members_list.size[0], mbr_item.line_height + mbr_item.line_spacing + mbr_item.padding[1] + mbr_item.padding[3]
        members_list.add_widget(mbr_item)

        rt_body.add_widget(members_list)
        rb_body = ScrollView(size_hint=(1, 0.5))
        self.rooms_list = rooms_list = GridLayout(
            cols=1,
            spacing=1,
            size_hint_y=None,
        )
        rooms_list.bind(minimum_height=rooms_list.setter('height'))
        #test item
        rm_item = TextInput(text="Nothing", size_hint_y=None, height=20, background_color=choice(COLORS), readonly=True)
        rm_item.size = rooms_list.size[0], rm_item.line_height + rm_item.line_spacing + rm_item.padding[1] + rm_item.padding[3]
        rooms_list.add_widget(rm_item)

        rb_body.add_widget(rooms_list)
        right_pane.add_widget(rt_body)
        right_pane.add_widget(rb_body)
        body.add_widget(left_pane)
        body.add_widget(right_pane)
        root.add_widget(body)
        self.postbuf = postbuf = GridLayout(
            cols=1,
            rows=2,
            spacing=1,
            size_hint=(1, platform('linux', 0.3, 0.5)),
        )
        self.textbuf = textbuf = TextBuffer(text=u'', size_hint=(1, 0.9))
        postbuf.add_widget(textbuf)
        root.add_widget(postbuf)
        if platform('android', True, False):
            self.empty = empty = Label(size_hint_y=None)
        else:
            self.empty = empty = Label(size_hint_y=0)
        root.add_widget(empty)
        self.add_widget(root)

    def notify(self, message):
        app.window.infobar.text = message

############################
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

    def _focus(self, instance, value):
        if platform('android', True, False):
            if value:
                app.window.empty.size = Window.width, Window.keyboard_height
            else:
                app.window.empty.size = Window.width, 0

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

    def insert_text(self, substring, from_undo=False):
        std_ins = TextInput.insert_text
        if len(substring) == 1:
            line = self._lines[self.cursor_row]
            if substring ==  u'\n':
                
                # Try find commands:
                if line.split(' ', 1)[0] in COMMANDS:
                    try:
                        resp = exec_cmd(*(line + ' ').split(' ', 1)[:2])
                    except Exception, err:
                            app.window.notify(err.message)
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
                                except net.API.MatrixRequestError, err:
                                    app.window.notify(err.message)
                                except AttributeError:
                                    pass
                            else:
                                std_ins(self, substring, from_undo)
                        else:
                            std_ins(self, substring, from_undo)
                    except NameError, err: print err
            else:
                std_ins(self, substring, from_undo)
        else:
            std_ins(self, substring, from_undo)

#
class Search(Screen):
    """
    """
    def __init__(self, **kwa):
        super(Screen, self).__init__(**kwa)
        self.root = root = GridLayout(cols=1, rows=5)
        self.add_widget(root)

#####################
class MatrixApp(App):
    """
    """
    def __init__(self):
        pass

    def build(self):
        root = ScreenManager(transition=SlideTransition(direction='up'))
        root.fullscreen = True
        root.orientation = "auto"
        
        root.user_id, root.password, root.current_room_alias, root.server, root.predefined_rooms = load_settings()
        room = Room(name=root.current_room_alias)
        root.add_widget(room)
        for room in root.predefined_rooms:
            room = Room(name=room)
            root.add_widget(room)
        try:
            root.client, root.access_token = net.sign_in_matrix(root.server, root.user_id, root.password)
            root.current_room = root.client.join_room(root.current_room_alias)
            root.current_room.add_listener(room_callback)
            root.current_room.user_ids = []
            root.client.add_listener(user_callback)
            root.client.start_listener_thread()
        except net.API.MatrixRequestError, err:
            pass
        root.window = root.current_screen
        return root

    def on_pause(self):
        return True

    def on_resume(self):
        return True

    def on_exit(self):
        return True

def global_keyboard_callback(key, scancode, codepoint, modifiers):
    #print 'key:', key, 'scancode:', scancode, 'codepoint:', repr(codepoint), 'modifiers:', modifiers
    if modifiers:
        if 'ctrl' in modifiers:

            # <Ctrl><Tab>: autocomplete
            if key == 9:
                if app.window.textbuf.focus:
                    app.window.textbuf.autocomplete()

            # <Ctrl><Backspace>: backspace word
            if key == 8:
                if app.window.textbuf.focus:
                    textbuf = app.window.textbuf
                    separators = ' ,.:;<>\'"([{}])'
                    col = textbuf.cursor_col
                    line = textbuf._lines[textbuf.cursor_row]
                    pos = max(line.rfind(s, 0, col) for s in separators) + 1
                    for i in line[pos:col]: textbuf.do_backspace()

            # <Ctrl><Enter>: send message
            elif key == 13:
                if app.window.textbuf.focus:
                    try:
                        textbuf = app.window.textbuf
                        resp = app.current_room.send_text(textbuf.text[:-1])
                        textbuf.text = ''
                        if isinstance(resp, dict):
                            app.window.notify(resp[u'event_id'])
                    except net.API.MatrixRequestError, err:
                        app.window.notify(err.message)
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
                if not app.window.textbuf.focus:
                    app.current = app.previous()
                    #app.current_room = [r for r in app.client.get_rooms().values() if r.name == app.window.name][0]

            # <Ctrl><`>`>: switch to next room
            elif key == 275:
                if not app.window.textbuf.focus:
                    app.current = app.next()
                    #app.current_room = [r for r in app.client.get_rooms().values() if r.name == app.window.name][0]

            # <Ctrl><e>: switch to message buffer
            elif key == 101:
                if not app.window.textbuf.focus:
                    textbuf = app.window.textbuf
                    app.window.textbuf.focus = True
                    textbuf.insert_text(' ')
                    textbuf.do_backspace()

    #return True
Window.on_keyboard = global_keyboard_callback

##########################
if __name__ == '__main__':
    app = MatrixApp().build()
    app.client._sync(limit=10)
    for m in (
        "test" * 50 + '\n' + "press" * 5 + '\n' + "stop" * 50,
        "test" * 50 + '\n' + "press" * 5 + '\n' + "stop" * 50,
        "test" * 50 + '\n' + "press" * 5 + '\n' + "stop" * 50,
        ): update_timeline(app.window.timeline, m)
    runTouchApp(app)
