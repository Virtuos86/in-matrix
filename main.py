# coding: utf-8
#qpy:kivy

'''
'''

from __future__ import print_function
from functools import partial

__author__ = "Szia <@szia:matrix.org>"
DEBUG = True
ACTIVITYPORT = 3001
SERVICEPORT = 3000

def _(text):
    #TODO
    if isinstance(text, unicode):
        return text
    return text.decode('utf-8')

def platform(predicate, true, false):
    if kivy.platform == predicate:
        return true
    else:
        return false

APP_TITLE = u"In-Matrix (IM)"
PATH_TO_HISTORY = u'./history'
SETTINGS = {
    'ui': {
        'colors': {
            'window-color': (1, 1, 1, 1),
        }
    }
}
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

    '!help',  # help
    '!clear', # clear timeline
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
from threading import Thread
from random import choice
import pprint
import codecs
import gzip
import json
import datetime
import os
import kivy
from kivy.core.window import Window as _Window

# _Window.keyboard_height (and _Window.on_keyboard) was added in 1.9
if platform('android', True, False):
    if int(kivy.__version__.split('.')[1]) > 8:
        kivy.require('1.9.0')
    else:
        kivy.require('1.8.0')
        _Window.keyboard_height = _Window.height / 2
    from android import AndroidService, wait_for_resume
else:
    kivy.require('1.8.0')


from kivy.lib import osc
from kivy.clock import Clock
from kivy.metrics import sp
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
from kivy.uix.screenmanager import (WipeTransition, FadeTransition, NoTransition,
                                   FallOutTransition, SwapTransition, SlideTransition,
                                   RiseInTransition)
from kivy.properties import (NumericProperty, BooleanProperty, AliasProperty, 
                            ObjectProperty, ListProperty, 
                            ReferenceListProperty, OptionProperty)
from kivy.uix.popup import Popup
from kivy.config import Config
from kivy.base import runTouchApp
from kivy.app import App
from kivy.lang import Builder

import net

##########################################

##############
class _Worker:
    """
    """
    def __init__(self):
        self.handler = Thread(target=self._worker)
        self.queue = []

    def _worker(self):
        if self.queue:
            if not self.handler.isAlive():
                self.queue.pop()
            else:
                task = self.queue.pop()
                task()
Worker = _Worker()
Worker.handler.start()

def load_settings():
    global SETTINGS, FONTS
    with open('settings.json') as f:
        s = json.load(f)
        try:
            s["matrix"]["password"] = s["matrix"]["password"].decode('base64')
        except:
            pass
    SETTINGS = s
    FONTS = s['ui']['fonts']
    return SETTINGS

try:
    load_settings()
except Exception, err:
    open('post-mortem.log', 'w').write("Fail loading settings.")
_Window.clearcolor = SETTINGS['ui']['colors']['window-color']
_Window.set_icon('./res/img/icon.png')

def store_settings():
    with open('settings.json', 'w') as f:
        json.dump(SETTINGS)
    return True

def load_history(room_alias):
    path = os.path.join(PATH_TO_HISTORY, room_alias, 'allhistory')
    if not os.path.exists(path):
        os.makedirs(os.path.join(PATH_TO_HISTORY, room_alias))
        return u''
    with gzip.open(path, 'rb') as hfile:
        return hfile.read().decode('utf-8')

def store_history(room_id, content):
    path = os.path.join(PATH_TO_HISTORY, room_id, 'allhistory')
    if not os.path.exists(path):
        os.makedirs(os.path.join(PATH_TO_HISTORY, room_id))
    with gzip.open(path, 'ab') as hfile:
        hfile.write(content.encode('utf-8'))

def update_timeline(timeline, content=None):
    if content is None:
        timeline.add_widget(Label(text="[b]. . .[/b]", markup=True, size_hint_y=None, height=20))
    else:
        msg = TextInput(text=content,
            size_hint_y=None,
            font_name=FONTS['timeline'],
            readonly=True,
        )
        msg.background_color = choice(COLORS) if SETTINGS['ui']['flags']['enable-item-random-color'] else (1, 1, 1, 1)
        msg.foreground_color = [0, 0, 0, 1]
        
        # TODO >_<
        msg.size = (_Window.width, 
            msg.line_height * len(content.splitlines())
            + msg.line_spacing * (len(content.splitlines()) - 1)
            + msg.padding[1] + msg.padding[3])
        timeline.add_widget(msg)

def exec_cmd(cmd, data):
    resp = ''
    if cmd == '/nick':
        pass
    elif cmd == '/me':
        resp = app.current_screen.room.send_emote(data)
    elif cmd == '/join':
        try:
            if data:
                resp = app.client.join_room(data)
                app.current_screen.name = data
            else:
                resp = app.client.join_room(app.current_screen.name)
        except Exception, err:
            app.current_screen.infobar.text = err.message
    elif cmd == '/leave':
        resp = app.current_screen.room.leave(app.user_id)
    elif cmd == '/kick':
        user_id, reason = (data + ' ').split(' ', 1)[:2]
        resp = app.current_screen.room.kick_user(user_id, reason)
    elif cmd == '/ban':
        user_id, reason = (data + ' ').split(' ', 1)[:2]
        resp = app.current_screen.room.ban_user(user_id, reason)
    elif cmd == '/unban':
        pass
    elif cmd == '/op':
        pass
    elif cmd == '/deop':
        pass
    elif cmd == '!help':
        update_timeline(app.current_screen.timeline, open('./HELP').read())
    elif cmd == '!clear':
        timeline = app.current_screen.timeline
        while timeline.children:
            timeline.remove_widget(timeline.children[-1])

    return resp

def parse_membership(event):
    # TODO
    pass

def parse_msg(event):
    e = event
    etype = e[u"type"]
    screen = [screen for screen in app.screens if not screen.special and screen.room.room_id == e['room_id']][0]
    if u'membership' in e:
        content = e['content']
        update_timeline(screen.timeline, _("%s has %s.") % (
            content[u'displayname'], {"leave": _("left"), "join": _("joined")}[content['membership']]
            )
        )
    #if (e["user_id"] == app.user_id or e["content"]["msgtype"] == "m.notice"):
    #    return
    if etype == u'm.room.message':
        if u'body' in e[u'content']:
            update_timeline(screen.timeline, "[%s/%s] %s:\n%s" % (
                e[u'age'],
                datetime.datetime.fromtimestamp(int(e["origin_server_ts"] / 1000)).strftime('%d-%m-%Y %H:%M:%S'),
                e[u'user_id'],
                e[u'content'][u'body'])
            )
    elif etype == u'm.typing':
        app.current_screen.notify(
            ", ".join(
                e[u'content'][u'user_ids'] or (_("You"),)) + _(" type(s) a message(s).")
        )
    elif etype == u'm.presence':
        if u'displayname' in e[u'content']:
            user_id, user_ids = e[u'content'][u'displayname'], app.current_screen.room.user_ids
            if user_id not in user_ids:
                user_ids.append(user_id)
    else:
        update_timeline(screen.timeline, unicode(e))

def room_callback(event):
    if event[u'type'] != 'm.typing':
        open('common_log', 'w').write(pprint.pformat(event) + '\n\n\n')
    e = event
    etype = e[u'type']
    switch = {
        u"m.room.member"          : parse_membership,
        u"m.room.message"         : parse_msg,
        u"m.room.message.feedback": lambda event: None,
        u"m.room.topic"           : parse_msg,
        u"m.room.name"            : parse_msg,
        u"m.room.invite"          : parse_msg,
        u"m.room.join"            : parse_msg,
        u"m.room.leave"           : parse_msg,
        u"m.room.ban"             : parse_msg,
        u"m.typing"               : parse_msg,
    }
    try:
        switch[etype]
    except KeyError, err:
        print("room_callback", etype)
    parse_msg(event)

# TODO
user_callback = lambda event: None

########################
class PopupLabel(TextInput):
    """
    """
    def __init__(self, full_text_callback, **kwargs):
        if 'full_text' in kwargs:
            self.full_text = kwargs['full_text']
        self.full_text_callback = full_text_callback
        self.default_text = kwargs['text']
        self.default_size_hint_y = kwargs['size_hint_y']
        self.text_size = (_Window.width, None)
        self.is_opened = False
        self.bind(focus=self._focus)
        TextInput.__init__(self, **kwargs)

    def do_popup(self):
        if self.is_opened:
            self.size_hint_y = self.default_size_hint_y
            self.text = self.default_text
            self.size = (_Window.width,  
                self.line_height * len(self._lines)
                + self.line_spacing * (len(self._lines) - 1)
                + self.padding[1] + self.padding[3])
            self.is_opened = False
        else:
            self.size_hint_y = None
            self.text = self.full_text_callback(self)
            self.size = (_Window.width,  
                self.line_height * len(self._lines)
                + self.line_spacing * (len(self._lines) - 1)
                + self.padding[1] + self.padding[3])
            self.is_opened = True
        return True

    @staticmethod
    def _focus(self, touch):
        return self.do_popup()

def info_for_app_title():
    room = app.current_screen.room
    title = room.name if room.name is not None else (room.aliases[0] if room.aliases else app.current_screen.name)
    description = room.topic if room.topic is not None else _("<this room hasn't any topic>")
    return title, description

###################
class Window(Screen):
    """
    """
    special = False

    def __init__(self, **kwargs):
        super(Window, self).__init__(**kwargs)
        self.root = root = GridLayout(cols=1, rows=5)
        self.title = PopupLabel(
            full_text_callback=lambda self: u"%s\n\n%s" % info_for_app_title(),
            text=self.name,
            multiline=True,
            bold=True,
            background_color=SETTINGS['ui']['colors']['title-color']['bg'],
            size_hint_y=platform('linux', 0.03, 0.1),
            readonly=True,
        )
        root.add_widget(self.title)
        self.infobar = PopupLabel(
            full_text_callback=lambda self: self.full_text,
            text=u". . .",
            full_text=u"t\ne\ns\nt",
            multiline=True,
            size_hint_y=platform('linux', 0.03, 0.1),
            background_color=SETTINGS['ui']['colors']['infobar-color']['bg'],
            font_name=FONTS['infobar'],
        )
        root.add_widget(self.infobar)
        self.body = body = GridLayout(cols=2, rows=1, size_hint_y=0.5)
        body.spacing = 1, 0
        self.left_pane = left_pane = ScrollView(size_hint_x=0.9)
        self.timeline = timeline = GridLayout(
            cols=1,
            spacing=1,
            size_hint_y=None,
        )
        timeline.bind(minimum_height=timeline.setter('height'))
        left_pane.add_widget(timeline)
        self.right_pane = right_pane = GridLayout(cols=1, rows=2, size_hint_x=0.1)
        right_pane.spacing = 0, 5
        rt_body = ScrollView(size_hint=(1, 0.7))
        self.members_list = members_list = GridLayout(
            cols=1,
            spacing=1,
            size_hint_y=None,
        )
        members_list.bind(minimum_height=members_list.setter('height'))
        mbr_item = TextInput(
            text=_("Members:"),
            size_hint_y=None,
            height=20,
            background_color=choice(COLORS) if SETTINGS['ui']['flags']['enable-item-random-color'] else (1, 1, 1, 1),
            readonly=True
        )
        mbr_item.size = members_list.size[0], mbr_item.line_height + mbr_item.line_spacing + mbr_item.padding[1] + mbr_item.padding[3]
        members_list.add_widget(mbr_item)

        rt_body.add_widget(members_list)
        rb_body = ScrollView(size_hint=(1, 0.3))
        self.rooms_list = rooms_list = GridLayout(
            cols=1,
            spacing=1,
            size_hint_y=None,
        )
        rooms_list.bind(minimum_height=rooms_list.setter('height'))
        rm_item = TextInput(
            text=_("Rooms:"),
            size_hint_y=None,
            height=20,
            background_color=choice(COLORS) if SETTINGS['ui']['flags']['enable-item-random-color'] else (1, 1, 1, 1),
            readonly=True
        )
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
            rows=1,
            spacing=1,
            size_hint_y=None,
        )
        self.textbuf = textbuf = TextBuffer(text=u'')
        postbuf.add_widget(textbuf)
        root.add_widget(postbuf)
        if platform('android', True, False):
            self.empty = empty = Label(size_hint_y=0)
            self.empty.size = _Window.width, 0
            root.add_widget(empty)
        else:
            self.empty = empty = Label(size_hint_y=0)
            self.empty.size = _Window.width, 0
            root.add_widget(empty)
        self.add_widget(root)

    def notify(self, message, full_message=None):
        self.infobar.text = message
        if full_message is not None:
            self.infobar.full_text = full_message
        else:
            self.infobar.full_text = u""

############################
class TextBuffer(TextInput):
    """
    """
    def __init__(self, **kwargs):
        super(TextBuffer, self).__init__(**kwargs)
        self.hint_text = _('Type here! Press <M><Enter> or <Enter><Enter> to send a message.')
        self.size_hint_y = None
        self.min_size = _Window.width, self.line_height * 3 + self.line_spacing * 2 + self.padding[1] + self.padding[3]
        #self.size = self.min_size
        self.auto_indent = True
        self.border = (10, 50, 50, 50)
        self.font_size = 20
        self.font_name = FONTS['post-buffer']
        self.background_color = [1, 1, 1, 1]
        self.foreground_color = [0.1, 0.2, 0.1, 1]
        self.cursor_color = [1, 1, 0, 1]
        self.bind(focus=self._focus)

    @staticmethod
    def _focus(self, value):
        if platform('android', True, False):
            if value:
                app.current_screen.empty.size_hint_y = 1
                app.current_screen.empty.size = _Window.width, _Window.keyboard_height
            else:
                app.current_screen.empty.size_hint_y = 0
                app.current_screen.empty.size = _Window.width, 0

    def autocomplete(self):
        line = self._lines[self.cursor_row]
        col = self.cursor_col
        pos = line.rfind(' ', 0, col)
        word = line[(0 if pos <= 0 else pos + 1):col]
        variants = []
        for user_id in app.current_screen.room.user_ids:
            if user_id.startswith(word):
                variants.append(user_id)
        else:
            if len(variants) == 1:
                s = super(TextBuffer, self)
                for i in word:
                    s.do_backspace()
                else:
                    self.insert_text(variants[0] + ': ')

    def resize(self):
        return
        # TODO! TODO! TODO!!!
        size_y = self.size[1]
        if self.text:
            self.size = (_Window.width, max(self.min_size[1], min(_Window.height / 3,
                self.line_height * len(self._lines)
                + self.line_spacing * (len(self._lines) - 1)
                + self.padding[1] + self.padding[3])))
        else:
            self.size = self.min_size
        ds = size_y - self.size[1]
        app.current_screen.body.size = app.current_screen.body.size[0], app.current_screen.body.size[1] + ds

    def do_backspace(self, from_undo=False, mode='bkspc'):
        self.resize()
        return super(TextBuffer, self).do_backspace(from_undo, mode)

    def insert_text(self, substring, from_undo=False):
        std_ins = TextInput.insert_text
        if len(substring) == 1:
            """try:
                Worker.queue.append(lambda: app.client.api.send_typing(app.current_screen.room.room_id, app.client.user_id))
                Worker.handler.run()
            except Exception, err:
                print(Exception, err)"""
            line = self._lines[self.cursor_row]
            if substring ==  u'\n':

                # Try find commands:
                if line.split(' ', 1)[0] in COMMANDS:
                    try:
                        resp = exec_cmd(*(line + ' ').split(' ', 1)[:2])
                    except Exception, err:
                            app.current_screen.notify(err.message)
                    else:
                        if isinstance(resp, dict):
                            app.current_screen.notify(resp[u'event_id'], unicode(resp))
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
                                        resp = app.current_screen.room.send_text(self.text[:-1])
                                        self.text = ''
                                        if isinstance(resp, dict):
                                            app.current_screen.notify(resp[u'event_id'])
                                    else:
                                        std_ins(self, substring, from_undo)
                                except net.API.MatrixRequestError, err:
                                    app.current_screen.notify(err.message)
                                except AttributeError:
                                    pass
                            else:
                                std_ins(self, substring, from_undo)
                        else:
                            std_ins(self, substring, from_undo)
                    except Exception, err: print(err)
                self.resize()
            else:
                std_ins(self, substring, from_undo)
        else:
            std_ins(self, substring, from_undo)
            self.resize()

# Screen for generic search (not implemented)
class Search(Screen):
    """
    """
    special = True

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)
        self.root = root = GridLayout(cols=1, rows=5)
        self.add_widget(root)

# Start screen
class PublicRoomsList(Screen):
    """
    """
    special = True

    def __init__(self, app, **kwargs):
        super(Screen, self).__init__(**kwargs)
        self.name = _(u"[Public rooms]")
        self.root = root = ScrollView()
        self.timeline = timeline = GridLayout(cols=1, size_hint_y=None)
        timeline.bind(minimum_height=timeline.setter('height'))
        root.add_widget(timeline)
        try:
            rooms_list = app.client.api.public_rooms()['chunk']
            rooms_list.sort(key=lambda i: i[u'num_joined_members'], reverse=True)
            if DEBUG:
                rooms_list = rooms_list[:50]
            for room in rooms_list:
                update_timeline(timeline, "%s [%d member(s)]\n\n%s" % (
                    (room[u'name'] + " (" + room[u'aliases'][0] + ")") if room[u'name'] is not None else room[u'aliases'][0],
                    room[u'num_joined_members'],
                    room[u'topic'] or _("<this room hasn't any topic>")
                    )
                )
        except net.API.MatrixRequestError, err:
            print(err.message)
        self.add_widget(root)


#####################
class MatrixApp(App):
    """
    """
    def __init__(self):
        pass

    def build(self):
        matrix = SETTINGS['matrix']
        self.icon = './res/img/icon.png'
        try:
            transition = globals()[SETTINGS['ui']['screen-transition']["transitions"][0]]
            direction = SETTINGS['ui']['screen-transition']['direction'][0]
        except:
            transition = NoTransition
            direction = 'up'
        root = ScreenManager(transition=transition(direction=direction))
        root.fullscreen = False
        root.orientation = "portrait"
        root.user_id = matrix['user_id']
        root.password = matrix['password']
        root.default_room_alias = matrix['default_room_alias']
        root.server = matrix['server']
        root.predefined_rooms = matrix['predefined_rooms']
        try:
            all_rooms = [root.default_room_alias] + root.predefined_rooms
            root.client, root.access_token = net.sign_in_matrix(root.server, root.user_id, root.password)
            root.add_widget(PublicRoomsList(app=root))
            for room in all_rooms:
                window = Window(name=room)
                window.room = root.client.join_room(room)
                window.room.add_listener(room_callback)
                window.room.user_ids = []
                root.add_widget(window)
                net.update_room_details(window.room)
        except net.API.MatrixRequestError, err:
            pass

        root.client.add_listener(user_callback)
        root.client.start_listener_thread()
        for screen in (screen for screen in root.screens if not screen.special):
            for scr in root.screens:
                rm_item = TextInput(text=scr.name, size_hint_y=None, height=20, background_color=(1, 1, 1, 1), readonly=True)
                rm_item.size = (screen.rooms_list.size[0], rm_item.line_height 
                               + rm_item.line_spacing + rm_item.padding[1] + rm_item.padding[3])
                screen.rooms_list.add_widget(rm_item)
        # O_o
        if DEBUG and platform('android', True, False):
            self.service_title = "In-Matrix"
            self.service_description = "*******"
            self.service = None
            self.start_new_service(self.service_title, self.service_description)
            osc.init()
            oscid = osc.listen(ipAddr='127.0.0.1', port=ACTIVITYPORT)
            osc.bind(oscid, self.callback, '/im')
            Clock.schedule_interval(lambda *x: osc.readQueue(oscid), 1)
        return root

    def start_new_service(self, title=None, description=None):
        if self.service is not None:
            self.service.stop()
            self.service = None
        service = AndroidService(
          title or self.service_title,
          description or self.service_description)
        service.start('service started')
        self.service = service

    def callback(self, msg, *args):
        if msg[2] == "+":
            self.start_new_service(*msg[:2])

    def on_start(self):
        pass

    def on_stop(self):
        return self.on_exit()

    def on_pause(self):
        return True

    def on_resume(self):
        return True

    def on_exit(self):
        '''for scr in self.root.screens:
            room = scr.room
            room.client.api.leave_room(room.room_id)'''
        return True

    def on_touch_move(self, touch):
        width, height = _Window.size
        if (touch.pos[0] - touch.spos[0]) > width / 4:
            app.current = app.previous()
        elif (touch.spos[0] - touch.pos[0]) > width / 4:
            app.current = app.next()

    def open_settings(self, *a):
        pass

def global_keyboard_callback(key, scancode, codepoint, modifiers):
    #print('key:', key, 'scancode:', scancode, 'codepoint:', repr(codepoint), 'modifiers:', modifiers)
    if modifiers:
        if SETTINGS['ui']['key-modifier'][0] in modifiers:

            # <M><Tab>: autocomplete
            if key == 9:
                if app.current_screen.textbuf.focus:
                    app.current_screen.textbuf.autocomplete()

            # <M><Backspace>: backspace word
            if key == 8:
                if app.current_screen.textbuf.focus:
                    textbuf = app.current_screen.textbuf
                    separators = ' ,.:;<>\'"([{}])'
                    col = textbuf.cursor_col
                    line = textbuf._lines[textbuf.cursor_row]
                    pos = max(line.rfind(s, 0, col) for s in separators) + 1
                    for i in line[pos:col]: textbuf.do_backspace()

            # <M><Enter>: send message
            elif key == 13:
                if app.current_screen.textbuf.focus:
                    try:
                        textbuf = app.current_screen.textbuf
                        try:
                            resp = app.current_screen.room.send_text(textbuf.text[:-1])
                        except UnicodeDecodeError, err:
                            app.current_screen.notify(_("Error decoding message!"))
                        textbuf.text = ''
                        if isinstance(resp, dict):
                            app.current_screen.notify(resp[u'event_id'])
                    except net.API.MatrixRequestError, err:
                        app.current_screen.notify(err.message)
                    except AttributeError:
                        pass

            # <M><1-9>: switch to room <№>
            elif key in (49,50,51,52,53,54,55,56,57):
                def callback(dt):
                    app.current = app.screens[min(key - 49, len(app.screens) - 1)].name
                Clock.schedule_once(callback)

            # <M><n>: create new window for joining new room
            elif key == 110:
                app.add_widget(Window(name=str(_gen_index.next())))

            # <M><t>: put focus in title
            elif key == 116:
                if not app.current_screen.textbuf.focus:
                    app.current_screen.title.focus = True

            # <M><i>: put focus in infobar
            elif key == 105:
                if not app.current_screen.textbuf.focus:
                    app.current_screen.infobar.focus = True

            # <M><`<`>: switch to previous room
            elif key == 276:
                if app.current_screen.special:
                    app.current = app.previous()
                elif not app.current_screen.textbuf.focus:
                    app.current = app.previous()

            # <M><`>`>: switch to next room
            elif key == 275:
                if app.current_screen.special:
                    app.current = app.next()
                elif not app.current_screen.textbuf.focus:
                    app.current = app.next()

            # <M><e>: switch to message buffer
            elif key == 101:
                if not app.current_screen.textbuf.focus:
                    textbuf = app.current_screen.textbuf
                    app.current_screen.textbuf.focus = True
                    textbuf.insert_text(' ')
                    textbuf.do_backspace()
    elif key == 273:
        if app.current == _("[Public rooms]"):
            prlist = app.current_screen
            m = sp(prlist.root.scroll_wheel_distance)
            e = prlist.root.effect_y
            e.value = max(e.value - m, e.min)
            e.velocity = 0
            e.trigger_velocity_update()
    elif key == 274:
        if app.current == _("[Public rooms]"):
            prlist = app.current_screen
            m = sp(prlist.root.scroll_wheel_distance)
            e = prlist.root.effect_y
            e.value = min(e.value + m, e.max)
            e.velocity = 0
            e.trigger_velocity_update()
    elif key == 280:
        if app.current == _("[Public rooms]"):
            prlist = app.current_screen
            m = sp(_Window.height)
            e = prlist.root.effect_y
            e.value = max(e.value - m, e.min)
            e.velocity = 0
            e.trigger_velocity_update()
    elif key == 281:
        if app.current == _("[Public rooms]"):
            prlist = app.current_screen
            m = sp(_Window.height)
            e = prlist.root.effect_y
            e.value = min(e.value + m, e.max)
            e.velocity = 0
            e.trigger_velocity_update()
    return True
_Window.on_keyboard = global_keyboard_callback

##########################
if __name__ == '__main__':
    app = MatrixApp().build()
    app.client._sync(limit=100)
    runTouchApp(app)
