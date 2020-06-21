from kivy.uix.floatlayout import FloatLayout
from screens.imageviewscreen import ImageViewScreen
from touchpadscreen import TouchPadScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView



class MainAppContainer(ScrollView):
    pass


class ScManager(ScreenManager):
    pass


class ConnInitScreen(Screen):
    pass


class PcCltTransScreen(Screen):
    import SimpleHTTPServer
    import SocketServer

    PORT = 8000

    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler


class MainScreen(Screen):
    pass


class KeyboardScreen(Screen):
    pass


