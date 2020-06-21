
import re

from kivy.app import App
from kivy.properties import BooleanProperty, NumericProperty, StringProperty, ObjectProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.modalview import ModalView
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.uix.screenmanager import RiseInTransition, NoTransition
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.uix.image import Image

# kivymd imports
from kivymd.theming import ThemeManager
from kivymd.bottomsheet import MDListBottomSheet
from kivymd.button import MDFloatingActionButton, MDIconButton, MDFlatButton
from kivymd.dialog import MDDialog
from kivymd.label import MDLabel

# TouchpadClient Package imports
from screens import MainAppContainer
from network import Protocol


class ProgressView(ModalView):
    # center: a, b (center of circle)
    center_a = NumericProperty()
    center_b = NumericProperty()
    active = BooleanProperty(True)
    w = NumericProperty(1.5)
    R = NumericProperty()
    adv = 1 / 30.
    start_deg = NumericProperty(60)
    stop_deg = NumericProperty(0)
    modalview_text = StringProperty('Please wait')

    def __init__(self, **kwargs):
        super(ProgressView, self).__init__(**kwargs)
        self.R = (self.width/8)
        self.event = None
        self.modal_text_update = None
        self.text_anim = []
        self.anim_text_pointer = 0
       
    def start(self):
        self.event = Clock.schedule_interval(self.rot_update, self.adv)
        self.modal_text_update = Clock.schedule_interval(self.loading, 0.7)
        self.active = True
        self.open()

    def loading(self, dt):
        if not self.text_anim:
            self.text_anim = [self.modalview_text, self.modalview_text+'.', self.modalview_text+'..',
                self.modalview_text+'...', self.modalview_text+'....']
        if self.anim_text_pointer > 4:
            self.anim_text_pointer = 0
        self.modalview_text = self.text_anim[self.anim_text_pointer]
        self.anim_text_pointer += 1

    def stop(self):
        self.modal_text_update.cancel()
        self.event.cancel()
        self.dismiss()
        self.active = False

    def rot_update(self, dt):
        self.stop_deg += 20
        self.start_deg = self.start_deg + 20
        if self.start_deg >= 420:
            self.start_deg = 60
            self.stop_deg = 0
            self.adv = 1/30.


class GridButton(MDFloatingActionButton):
    pass


class TouchpadApp(App):
    theme_cls = ThemeManager()

    bg_image = ObjectProperty(Image(source='images/apple-blogging-computer-34124.jpg', 
                                keep_ratio=True))
    touchpad_bg = ObjectProperty(Image(source='images/touchpad_bg.jpg', 
                                keep_ratio=True))

    help_button = MDFlatButton(text='help')

    settings_button = MDFlatButton(text='settings')

    menu_items = [
        {'viewclass': 'MDFlatButton',
         'text': 'help'},
        {'viewclass': 'MDFlatButton',
         'text': 'settings'},
    ]

    def __init__(self, **kwargs):
        super(TouchpadApp, self).__init__(**kwargs)
        self.app_menu = MDListBottomSheet()
        self.ip_addr_pattern = re.compile('[0-9]{1,3}')
        self.grid_button = None
        self.wait = None
        self.error_dialog = None
        self.current_screen_name = ''
        self.current_screen = None

        # initialization of communication protocol
        self.comm_protocol = Protocol()

    def build(self):
         Window.softinput_mode = 'below_target'
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.primary_hue = 'A400'
        self.build_grid_menu()
        self.grid_button = GridButton()
        self.grid_button.bind(on_release=self.show_grid_menu)
        self.grab_window_btn = MDFloatingActionButton()
        self.select_all_btn = MDFloatingActionButton()
        self.copy_btn = MDFloatingActionButton()
        self.cut_btn = MDFloatingActionButton()
        self.paste_btn = MDFloatingActionButton()
        self.ctrl_btn = MDFloatingActionButton()
        self.grab_window_btn.bind(on_release=self.enable_window_drag)
        self.select_all_btn.bind(on_release=self.do_select_all)
        self.copy_btn.bind(on_release=self.do_copy)
        self.cut_btn.bind(on_release=self.do_cut)
        self.paste_btn.bind(on_release=self.do_paste)
        self.ctrl_btn.bind(on_release=self.do_ctrl)
        return MainAppContainer()

    def add_menu_btn(self):
        if self.grid_button not in self.root.ids.icons_container.children:
            self.root.ids.icons_container.add_widget(self.grid_button)
        if self.ctrl_btn not in self.root.ids.floating_icons_container.children:
           self.ctrl_btn.icon = 'checkbox-multiple-marked-outline'
            self.ctrl_btn.pos_hint = {'right': 0.99}
            self.ctrl_btn.y = dp(273)
            self.ctrl_btn.elevation_normal = 1
            self.ctrl_btn.size = (dp(44), dp(43))
            self.ctrl_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.ctrl_btn.opacity = 1
            self.root.ids.floating_icons_container.add_widget(self.ctrl_btn)
        if self.grab_window_btn not in self.root.ids.floating_icons_container.children:
             self.grab_window_btn.icon = 'arrow-all'
            self.grab_window_btn.pos_hint = {'right': 0.99}
            self.grab_window_btn.y = dp(219)
            self.grab_window_btn.elevation_normal = 1
            self.grab_window_btn.size = (dp(44), dp(43))
            self.grab_window_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.grab_window_btn.opacity = 1
            self.root.ids.floating_icons_container.add_widget(self.grab_window_btn)
        if self.select_all_btn not in self.root.ids.floating_icons_container.children:
            self.select_all_btn.icon = 'select-all'
            self.select_all_btn.pos_hint = {'right': 0.99}
            self.select_all_btn.y = dp(165)
            self.select_all_btn.elevation_normal = 1
            self.select_all_btn.size = (dp(44), dp(43))
            self.select_all_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.select_all_btn.opacity = 1
            self.root.ids.floating_icons_container.add_widget(self.select_all_btn)
        if self.copy_btn not in self.root.ids.floating_icons_container.children:
           self.copy_btn.icon = 'content-copy'
            self.copy_btn.pos_hint = {'right': 0.99}
            self.copy_btn.y = dp(111)
            self.copy_btn.elevation_normal = 1
            self.copy_btn.size = (dp(44), dp(43))
            self.copy_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.copy_btn.opacity = 1
            self.root.ids.floating_icons_container.add_widget(self.copy_btn)
        if self.cut_btn not in self.root.ids.floating_icons_container.children:
            self.cut_btn.icon = 'content-cut'
            self.cut_btn.pos_hint = {'right': 0.99}
            self.cut_btn.y = dp(57)
            self.cut_btn.elevation_normal = 1
            self.cut_btn.size = (dp(44), dp(43))
            self.cut_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.cut_btn.opacity = 1
            self.root.ids.floating_icons_container.add_widget(self.cut_btn)
        if self.paste_btn not in self.root.ids.floating_icons_container.children:
            self.paste_btn.icon = 'content-paste'
            self.paste_btn.pos_hint = {'right': 0.99}
            self.paste_btn.y = dp(3)
            self.paste_btn.elevation_normal = 1
            self.paste_btn.size = (dp(44), dp(43))
            self.paste_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.paste_btn.opacity = 1
            self.root.ids.floating_icons_container.add_widget(self.paste_btn)

    def show_touchpad_ctrls(self):
       anim = Animation(pos_hint={'right': 1}, duration=0.2, t='in_quad')
        anim.start(self.root.ids.ct_sv)

    def hide_touchpad_ctrls(self):
       anim = Animation(pos_hint={'right':1+self.root.ids.ct_sv.width/Window.width}, duration=0.2, t='in_quad')
        anim.start(self.root.ids.ct_sv)

    def enable_window_drag(self, instance):
        try:
            if not self.toggle_dragbtn:
                self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::DRAG_WINDOW'
                self.grab_window_btn.md_bg_color = self.theme_cls.primary_color
                self.toggle_dragbtn = True
            else:
                self.grab_window_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_dragbtn = False
        except AttributeError:
            self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::DRAG_WINDOW'
            self.grab_window_btn.md_bg_color = self.theme_cls.primary_color
            self.toggle_dragbtn = True

    def do_select_all(self, instance):
        try:
            if not self.toggle_selectall:
                self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::SELECT_ALL'
                self.select_all_btn.md_bg_color = self.theme_cls.primary_color
                self.toggle_selectall = True
            else:
                self.select_all_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_selectall = False
        except AttributeError:
            self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::SELECT_ALL'
            self.select_all_btn.md_bg_color = self.theme_cls.primary_color
            self.toggle_selectall = True

    def do_copy(self, instance):
        try:
            if not self.toggle_copy:
                self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::COPY'
                self.copy_btn.md_bg_color = self.theme_cls.primary_color
                self.toggle_copy = True
                self.cut_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_cut = False
                self.paste_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_paste = False
            else:
                self.copy_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_copy = False
        except AttributeError:
            self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::COPY'
            self.copy_btn.md_bg_color = self.theme_cls.primary_color
            self.toggle_copy = True
            self.cut_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.toggle_cut = False
            self.paste_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.toggle_paste = False

    def do_cut(self, instance):
        try:
            if not self.toggle_cut:
                self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::CUT'
                self.cut_btn.md_bg_color = self.theme_cls.primary_color
                self.toggle_cut = True
                self.copy_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_copy = False
                self.paste_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_paste = False
            else:
                self.cut_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_cut = False
        except AttributeError:
            self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::CUT'
            self.cut_btn.md_bg_color = self.theme_cls.primary_color
            self.toggle_cut = True
            self.copy_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.toggle_copy = False
            self.paste_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.toggle_paste = False

    def do_paste(self, instance):
        try:
            if not self.toggle_paste:
                self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::PASTE'
                self.paste_btn.md_bg_color = self.theme_cls.primary_color
                self.toggle_paste = True
                self.copy_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_copy = False
                self.cut_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_cut = False
            else:
                self.paste_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_paste = False
        except AttributeError:
            self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::PASTE'
            self.paste_btn.md_bg_color = self.theme_cls.primary_color
            self.toggle_paste = True
            self.copy_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.toggle_copy = False
            self.cut_btn.md_bg_color = get_color_from_hex('#A0B0A8')
            self.toggle_cut = False
        
    def do_ctrl(self, instance):
        try:
            if not self.toggle_ctrl:
                self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::CTRL'
                self.ctrl_btn.md_bg_color = self.theme_cls.primary_color
                self.toggle_ctrl = True
            else:
                self.ctrl_btn.md_bg_color = get_color_from_hex('#A0B0A8')
                self.toggle_ctrl = False
        except AttributeError:
            self.root.ids.touchpad_screen.ids.touch_pad.comm_protocol.event = 'EVENT::CTRL'
            self.ctrl_btn.md_bg_color = self.theme_cls.primary_color
            self.toggle_ctrl = True

    def disable_btns_on_touch_touchpad(self):
        self.ctrl_btn.md_bg_color = get_color_from_hex('#A0B0A8')
        self.grab_window_btn.md_bg_color = get_color_from_hex('#A0B0A8')
        self.select_all_btn.md_bg_color = get_color_from_hex('#A0B0A8')
        self.toggle_dragbtn = False
        self.toggle_ctrl = False
        self.toggle_selectall = False
        
    def show_menu_btn(self, dt):
        if self.grid_button:
            anim = Animation(pos_hint={'x':0.019, 'y':0.019}, duration=0.2, t='in_quad')
            anim.start(self.grid_button)
            
    def hide_menu_btn(self):
        if self.grid_button:
            anim = Animation(pos_hint={'x':0.019, 'y':-self.grid_button.height/Window.height}, duration=0.2, t='in_quad')
            anim.start(self.grid_button)
            
    def build_grid_menu(self):
        self.app_menu.add_item("TouchPad", lambda x: self.change_screen('touchpad_screen'), icon='mouse')
        self.app_menu.add_item("Help", lambda x: self.change_screen('keyboard_screen'), icon='help')
        
    def show_grid_menu(self, instance):
        self.app_menu.open()

    def show_start_screen(self):
        # an interface that switches to the first screen just after the screen
        # that initializes the connection to a pc
        self.add_menu_btn()
        self.root.ids.sc_mgr.transition = RiseInTransition()
        self.root.ids.sc_mgr.current = 'touchpad_screen'

    def change_screen(self, screen_name, transition=NoTransition, direction='right'):
        self.remove_error_dialog()
        self.root.ids.sc_mgr.transition = transition()
        self.root.ids.sc_mgr.current = screen_name

    def check_addr(self, token):
        matched = 0
        if self.ip_addr_pattern.match(token) and len(token) <= 3:
            matched = 1
        return matched

    def init_connection(self):
        self.show_wait_dialog(self.root.ids.touchpad_screen, 'Connecting')
        self.comm_protocol.net_dcry_socket.establish_connection()

    def start_app(self):
        self.hide_wait_dialog()
        self.add_menu_btn()
        self.show_start_screen()

    def show_error_dialog(self, title='', text=None):
        # get current screen and show dilog on it
        # but before that ensure that request has not been cancelled
        # and the wait dialog is not active
        if self.error_dialog is None:

            content = MDLabel(font_style='Body1',
                              theme_text_color='Secondary',
                              text=text,
                              size_hint_y=None,
                              valign='top')
            content.bind(texture_size=content.setter('size'))
            self.error_dialog = MDDialog(title = title,
                                         md_bg_color=(1, 1, 1, 1),
                                         content=content,
                                         size_hint=(.8, None),
                                         height=dp(200),
                                         auto_dismiss=False)
            self.error_dialog.add_action_button("OK",
                                                action=lambda *x: self.change_screen('init_connection_screen'))
            self.error_dialog.open()

        self.hide_wait_dialog()

    def remove_error_dialog(self):
        if self.error_dialog is not None:
            self.error_dialog.dismiss()
            self.error_dialog = None

    def show_wait_dialog(self, parent, wait_text):
        self.remove_error_dialog()
        self.wait = ProgressView()
        self.wait.modalview_text = wait_text
        self.wait.attach_to = parent
        self.wait.start()

    def hide_wait_dialog(self):
        if self.wait:
            self.wait.stop()
            self.wait = None

    def on_pause(self):
        return True



TouchpadApp().run()