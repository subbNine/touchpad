import asyncore
import json
import socket
import netifaces

from kivy.app import App


# Network Discovery Socket
class NetControlSocket(asyncore.dispatcher):

    def __init__(self, comm_socket_instance):
        asyncore.dispatcher.__init__(self)
        self.main_comm_channel = comm_socket_instance
        self.port = 16590
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.set_socket(sock)
        self.keep_alive_stream = json.dumps({'who': 'PROTO::TOUCHPAD_CLT',
                                             'conn': 'SYN'})
        self.data = self.keep_alive_stream   # data assumed to be json string
        self.ret_data = ''
        self.decoded_data = ''
        self.count_null_returns = 0     # number of retries
        self.ip_address = None
        self.connection_established = False
        self.error_msg = ''
        self.running_app = App.get_running_app()
        self.enable_read = False
        
    def establish_connection(self):
        # get broadcast address. and search for pc endpoint
        try:
            # wlan0 is available if the user's wifi or hotspot is on
            interface_wlan = netifaces.ifaddresses('wlan0')
        except ValueError:
            self.running_app.show_error_dialog(title='Unable to connect!', text=
                                                'please ensure that your wifi or hotspot is turned on '
                                                'and connected to the same wireless network as PC.'
                                                )
        else:
            try:
                # netifaces.AF_INET is the key to the ipv4 interface.
                # a KeyError is raised if the user's wifi is on
                # but device not connected to a network; 
                # i.e the device has not been assigned an ip address
                ipv4_interface = interface_wlan[netifaces.AF_INET]
            except KeyError:
                # ERROR: you are not connected to a hotspot
                self.running_app.show_error_dialog(title='Unable to connect!', text=
                                                'please ensure that your wifi or hotspot is turned on '
                                                'and connected to the same wireless network as PC.'
                                                )
            else:
                broadcast_addr = ipv4_interface['broadcast']
                self.ip_address = (broadcast_addr, self.port)
                print('[SOCKET INFO] ', '(bcast, port): ', self.ip_address)
        
    def handle_connect(self):
        pass

    def readable(self):
        return self.enable_read

    def handle_write(self):
        self.count_null_returns = 0
        data = self.data
        # print(self.ip_address, self.data)
        try:
            sent = self.socket.sendto(data, self.ip_address)
        except socket.error:
            self.running_app.show_error_dialog(title='Could not find PC!', text=
                                                'please ensure that your mobile phone and PC are on the same network.'
                                                )
            self.disable_connection()
        else:
            print('[SENT PAYLOAD] ', self.data[:sent])
            self.data = self.data[sent:]
            self.enable_read = True

    def handle_read(self):
        # we're not dealing with large chunks of data
        data, address = self.socket.recvfrom(200)
        self.ret_data += data
        if address:
            self.ip_address = address

    def handle_close(self):
        if self.ret_data:
            print('[RECIEVED PAYLOAD] ', self.ret_data)
            self.decoded_data = json.loads(self.ret_data)
            self.ret_data = ''

			# connection successful.
            # give the ip address to socket that transmits touch signal
			# between phone and pc.
            if self.decoded_data.get('who') == 'PROTO::TOUCHPAD_SVR' and \
               self.connection_established is False:
                self.connection_established = True
                self.main_comm_channel.ip_address = self.ip_address[0]
                self.running_app.start_app()
                
            self.count_null_returns = 0
        else:
            self.count_null_returns += 1

        # after 10 tries without response
        # setup discovery connection to get the new pc address
        # by reinitializing the ip_address to '<broadcast>'
        if self.count_null_returns == 10:
            self.count_null_returns = 0
            # call an interface on the app to flag error in connection
            # or try to establish another connection
            # show error dialog
            print('[CONNECTION TIMEOUT] ', 'had', self.count_null_returns, 'tries')
            # after  10 tries re-establish the connection with a differnt ip address
            self.disable_connection()
            self.running_app.show_error_dialog(title ='PC did not respond!', text='Please ensure that your device ' 
                                               'and PC are connected to the same wireless network')
        
        self.data = self.keep_alive_stream

    def disable_connection(self):
        self.enable_read = False
        self.ip_address = None
        self.connection_established = False

    def enable_connection(self):
        self.enable_read = True
        self.data = self.keep_alive_stream

    def writable(self):
        return len(self.data) > 0 and self.ip_address


class DataTransferSocket(asyncore.dispatcher):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.port = 16591
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        self.set_socket(sock)
        self.keep_alive_stream = json.dumps({'who': 'PROTO::TOUCHPAD_CLT',
                                             'conn': 'SYN'})
        self.data = ''                    # data assumed to be json string
        self.ret_data = ''
        self.decoded_data = ''
        # number of times that we should expect a
        # handle_close method return with no (null) data before flagging error
        self.count_null_returns = 0
        self.ip_address = ''
        self.connection_established = None

    def handle_connect(self):
        pass

    def handle_write(self):
        data = self.data
        sent = self.socket.sendto(data, (self.ip_address, self.port))
        self.data = self.data[sent:]

    def readable(self):
        return False

    def writable(self):
        return len(self.data) > 0 and self.ip_address # not in ['', '<broadcast>']
