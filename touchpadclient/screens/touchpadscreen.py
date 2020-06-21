from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty
from kivy.effects.kinetic import KineticEffect
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.app import App



class TouchPad(BoxLayout):
    touched = BooleanProperty(None)
    swipe_started = BooleanProperty(False)
    trigger_on_touch_hold = None

    def __init__(self, **kwargs):
        super(TouchPad, self).__init__(**kwargs)
        self.widgets_kinetics = KineticEffect()
        self.touch_event_binder()
        self.running_app = App.get_running_app()
        self.comm_protocol = self.running_app.comm_protocol

    def touch_event_binder(self):
        self.bind(on_touch_down=self.tap)
        self.bind(on_touch_up=self.release)
        self.bind(on_touch_down=self.start_touch_hold)
        self.bind(on_touch_up=self.release_touch)
        self.bind(on_touch_move=self.swipe_start_marker)
        self.bind(on_touch_up=self.swipe_end_marker)

    # ----swipe  or touch_move event ----
    def swipe_start_marker(self, *args):
        touch = args[1]
        if self.collide_point(*touch.pos):
            if (touch.ox <= touch.x <= touch.ox + touch.dx
                or touch.ox - abs(2*touch.dx)
                    <= touch.x <= touch.ox) and self.swipe_started is False:
                self.widgets_kinetics.start(touch.ox)
                self.swipe_started = True
                touch.grab(self)
            # ----send touch_move event--
            self.comm_protocol.event = 'EVENT::TOUCH_MOVE'
            self.comm_protocol.cursor_pos = touch.dx, touch.dy
        return False

    def swipe_end_marker(self, *args):
        touch = args[1]
        if self.collide_point(*touch.pos):
            if self.swipe_started and touch.grab_current is self:
                self.widgets_kinetics.stop(touch.x)
                if self.widgets_kinetics.velocity >= 4000 and \
                        touch.x - 50 >= touch.ox:
                    self.comm_protocol.event = 'EVENT::SWIPE_RIGHT'
                if self.widgets_kinetics.velocity <= -4000 \
                        and touch.x + 50 <= touch.ox:
                    self.comm_protocol.event = 'EVENT::SWIPE_LEFT'
                self.swipe_started = False
        return False

    # ----touch hold event ----
    def start_touch_hold(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.touched = True
            self.trigger_on_touch_hold = Clock.schedule_once(
                lambda dt: self.on_touch_hold(dt, instance, touch), 0.68)
        return False

    def release_touch(self, instance, touch):
        if self.collide_point(*touch.pos):
            if self.trigger_on_touch_hold is not None:
                self.trigger_on_touch_hold.cancel()
                self.trigger_on_touch_hold = None
            self.touched = False
        return False

    def on_touch_hold(self, *args):
        touch = args[2]
        # allow for some jittering abs(0.1) is an arbitrary number
        if self.collide_point(*touch.pos):
            if self.touched and -0.1 <= touch.x - touch.ox <= 0.1 and \
                    -0.1 <= touch.y - touch.oy <= 0.1:
                # -----the protocol should be packed for a touch hold event
                self.comm_protocol.event = 'EVENT::TOUCH_HOLD'
            if self.trigger_on_touch_hold is not None:
                self.trigger_on_touch_hold.cancel()
                self.trigger_on_touch_hold = None

    # ----click event ----
    def tap(self, *args):
        touch = args[1]
        if self.collide_point(*touch.pos):
            self.comm_protocol.event = 'EVENT::TOUCH_DOWN'
            touch.grab(self)
        return True

    # a click event is registered when the time
    # inteval between tap and release is less than or equal to 0.15s
    def release(self, *args):
        touch = args[1]
        retval = False
        if self.collide_point(*touch.pos):
            if touch.grab_current is self and \
                    touch.time_end - touch.time_start <= 0.16:
                # -----the protocol should be packed for a click event
                # - touch.time_start)
                touch.ungrab(self)
                self.comm_protocol.event = 'EVENT::TOUCH_UP_'
                retval = True
            elif touch.grab_current is self and \
                    touch.time_end - touch.time_start > 0.16:
                touch.ungrab(self)
                self.comm_protocol.event = 'EVENT::TOUCH_UP'
                retval = True
            self.running_app.disable_btns_on_touch_touchpad()
        return retval

# this isnt useful in the app
class ScrollBar(BoxLayout):
    touched = BooleanProperty(None)
    swipe_started = BooleanProperty(False)
    trigger_on_touch_hold = None

    def __init__(self, **kwargs):
        super(ScrollBar, self).__init__(**kwargs)
        self.comm_protocol = Protocol()

    # ----swipe  or touch_move event ----
    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            if touch.oy <= touch.y:
                self.comm_protocol.event = 'EVENT::SCROLL_UP'
            else:
                self.comm_protocol.event = 'EVENT::SCROLL_DOWN'
            self.comm_protocol.cursor_pos = touch.dx, touch.dy
            return True



class TouchPadScreen(Screen):

    def __init__(self, **kwargs):
        super(TouchPadScreen, self).__init__(**kwargs)

