from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty
from kivy.effects.kinetic import KineticEffect
from kivy.clock import Clock

from network import Protocol


class ImageViewScreen(Screen):
    # time, t1, when the screen was clicked
    touched = BooleanProperty(None)
    swipe_started = BooleanProperty(False)
    trigger_on_touch_hold = None

    def __init__(self, **kwargs):
        super(ImageViewScreen, self).__init__(**kwargs)
        self.widgets_kinetics = KineticEffect()
        self.touch_event_binder()
        self.comm_protocol = Protocol()

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
        if (touch.ox <= touch.x <= touch.ox + touch.dx
            or touch.ox - abs(touch.dx)
           <= touch.x <= touch.ox) and self.swipe_started is False:
            self.widgets_kinetics.start(touch.ox)
            self.swipe_started = True
            touch.grab(self)
        # ----send touch_move event--
        self.comm_protocol.event = 'EVENT::TOUCH_MOVE'
        self.comm_protocol.cursor_pos = touch.dx, touch.dy
        return True

    def swipe_end_marker(self, *args):
        touch = args[1]
        if self.swipe_started and touch.grab_current is self:
            self.widgets_kinetics.stop(touch.x)
            if self.widgets_kinetics.velocity >= 4000 and  \
               touch.x - 50 >= touch.ox:
                # print('A right swipe has occured')
                self.comm_protocol.event = 'EVENT::SWIPE_LEFT'
            if self.widgets_kinetics.velocity <= -4000 \
               and touch.x + 50 <= touch.ox:
                # print('A left swipe has occured')
                self.comm_protocol.event = 'EVENT::SWIPE_RIGHT'
            # print(self.widgets_kinetics.velocity)
            self.swipe_started = False
        return False

    # ----touch hold event ----
    def start_touch_hold(self, instance, touch):
        self.touched = True
        self.trigger_on_touch_hold = Clock.schedule_once(
            lambda dt: self.on_touch_hold(dt, instance, touch), 0.68)
        return False

    def release_touch(self, *args):
        if self.trigger_on_touch_hold is not None:
            self.trigger_on_touch_hold.cancel()
            self.trigger_on_touch_hold = None
        self.touched = False
        return False

    def on_touch_hold(self, *args):
        touch = args[2]
        # allow for some jittering abs(0.1) is an arbitrary number
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
        touch.grab(self)
        return True

    # a click event is registered when the time
    # inteval between tap and release is less than or equal to 0.15s
    def release(self, *args):
        touch = args[1]
        if touch.grab_current is self and  \
           touch.time_end - touch.time_start <= 0.15:
            # -----the protocol should be packed for a click event
            # - touch.time_start)
            self.comm_protocol.event = 'EVENT::CLICK'
            touch.ungrab(self)
        return True
