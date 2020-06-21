import json
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.uix.widget import Widget
from kivy.properties import OptionProperty, ReferenceListProperty, NumericProperty  # StringProperty, BooleanProperty


from network.networksocket import NetControlSocket, DataTransferSocket


class Protocol(Widget, EventDispatcher):
    event = OptionProperty(None, allownone=True,
                           options=['EVENT::SWIPE_LEFT', 'EVENT::SWIPE_RIGHT', 'EVENT::KEYBOARD_DOWN',
                                    'EVENT_PV::SWIPE_LEFT', 'EVENT::TOUCH_UP', 'EVENT::TOUCH_UP_', 'EVENT::KEYBOARD_UP',
                                    'EVENT_PV::SWIPE_RIGHT', 'EVENT::TOUCH_DOWN', 'EVENT::SCROLL_UP',
                                    'EVENT::COPY', 'EVENT::CUT', 'EVENT::PASTE', 'EVENT::SELECT_ALL',
                                    'EVENT::DRAG_WINDOW','EVENT::SCROLL_DOWN', 'EVENT::TOUCH_MOVE',
                                    'EVENT::TOUCH_HOLD','EVENT::CTRL'])
    cursor_pos_dx = NumericProperty(0)
    cursor_pos_dy = NumericProperty(0)

    cursor_pos = ReferenceListProperty(cursor_pos_dx, cursor_pos_dy)
    keyboard_event_data = ''

    def __init__(self, **kwargs):
        super(Protocol, self).__init__(**kwargs)
        self.data_transfer_socket = DataTransferSocket()
        self.net_dcry_socket = NetControlSocket(self.data_transfer_socket)
        # asyncore.loop(timeout=1.0)
        self.dt = 0.1
        self.socket_worker = Clock.schedule_interval(
            lambda dt: self.socket_walk(
                self.net_dcry_socket,
                self.data_transfer_socket), self.dt)

    def socket_walk(sock1, sock2):
        s1 = sock1
        s2 = sock2
        s1_w = s1.writable()
        s2_w = s2.writable()
        if s1_w:
            s1.handle_write()
        if s2_w:
            s2.handle_write()
        s1_r = s1.readable()
        s2_r = s2.readable()
        if s1_r:
            try:
                s1.handle_read()
            except:
                s1.handle_close()
        if s2_r:
            s2.handle_read()

    def pack(self, payload):
        data = json.dumps(payload)
        self.data_transfer_socket.data = data

    def set_keyboard_event(self, keyboard_data, event):
        self.keyboard_event_data = keyboard_data
        self.event = event

    def on_event(self, *args):
        value = args[1]
        if value not in ['EVENT::TOUCH_MOVE', 'EVENT::SCROLL_UP', 'EVENT::SCROLL_DOWN'] and value is not None:
            # print(value)
            if value == 'EVENT::KEYBOARD_DOWN' or value == 'EVENT::KEYBOARD_UP':
                data = {'who': 'PROTO::TOUCHPAD_CLT', 'event_type': value,
                        'value': self.keyboard_event_data}
            else:
                data = {'who': 'PROTO::TOUCHPAD_CLT', 'event_type': value}
            self.pack(data)
            self.event = None
        return True

    def on_cursor_pos(self, *args):
        value = args[1]
        if self.event in ['EVENT::TOUCH_MOVE', 'EVENT::SCROLL_UP', 'EVENT::SCROLL_DOWN']:
            # pack the protocol
            data = {'who': 'PROTO::TOUCHPAD_CLT', 'event_type': self.event,
                    'value': {'dx': self.cursor_pos_dx, 'dy': self.cursor_pos_dy}}
            self.pack(data)
            print(data)
