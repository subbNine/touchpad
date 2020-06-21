import socket
import asyncore
import json
import pyautogui
import time
pyautogui.FAILSAFE = False
# from kivy.clock import Clock


	# Network Discovery Socket
class KeepAliveSocket(asyncore.dispatcher):

	def __init__(self, comm_socket_instance):
		asyncore.dispatcher.__init__(self)
		self.main_comm_channel = comm_socket_instance
		self.port = 16590
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		sock.setblocking(0)
		sock.bind(('', 16590))
		self.set_socket(sock)
		self.keep_alive_stream = json.dumps({'who': 'PROTO::TOUCHPAD_SVR',
											'conn': 'SYN-ACK'})
		self.data = ''                 # data assumed to be json string
		self.ret_data = ''
		self.decoded_data = ''
		# number of times that we should expect a
		# handle_close method return with no (null) data before flagging error
		self.count_null_returns = 0
		self.ip_address = ''
		self.connection_established = None

	def handle_connect(self):
		pass

	def readable(self):
		return True

	def handle_write(self):
		# redundant because of the writable() method
		# but the double-check is not bad
		if self.data:
			self.count_null_returns = 0
			data = self.data
			sent = self.socket.sendto(data, (self.ip_address))
			self.data = self.data[sent:]

	def handle_read(self):
		# we're not dealing with large chunks of data
		data, address = self.socket.recvfrom(200)
		self.ret_data += str(data)
		# print((self.ret_data, address))
		if address:
			self.ip_address = address

	def handle_close(self):
		# print((self.ret_data))
		if self.ret_data and self.ip_address:
			self.data = self.keep_alive_stream
			self.ret_data = ''

	def writable(self):
		return len(self.data) > 0


# forked socket
class DataTransferSocket(asyncore.dispatcher):
	def __init__(self):
		asyncore.dispatcher.__init__(self)
		# self.main_comm_channel = comm_socket_instance
		self.port = 16591
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setblocking(0)
		sock.bind(('', 16591))
		# sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.set_socket(sock)
		self.keep_alive_stream = json.dumps({'who': 'PROTO::TOUCHPAD_SVR',
											 'conn': 'SYN-ACK'})
		self.data = ''                    # data assumed to be json string
		self.ret_data = ''
		self.decoded_data = ''
		# number of times that we should expect a
		# handle_close method return with no (null) data before flagging error
		self.count_null_returns = 0
		self.ip_address = ''
		self.connection_established = None
		self.click_start_time = 0
		self.click_end_time = 0
		self.single_clicked = False
		self.drag_event_enabled = False
		self.click_time = None
		self.moved = False

	def handle_connect(self):
		pass


	def readable(self):
		return True

	def handle_read(self):
		# we're not dealing with large chunks of data
		data, address = self.socket.recvfrom(200)
		self.ret_data += data
		self.ip_address = address

	def handle_close(self):
		if self.ret_data:
			# print('data_transfer socket: ', self.ret_data)
			try:
				print(self.ret_data)
				data = json.loads(self.ret_data)
			except ValueError:
				pass
			else:
				event_type = data['event_type']
				if event_type == 'EVENT::TOUCH_MOVE':
					dx = float(data['value']['dx'])
					dy = -1 * float(data['value']['dy']) 
					scale_x = 1 if dx*dx<=2.5 else 4
					scale_y = 1 if dy*dy<=2.5 else 4
					dx = dx * scale_x
					dy = dy * scale_y
					if self.drag_event_enabled:
						if self.moved is False:
							pyautogui.mouseDown()
							self.moved = True
						pyautogui.moveRel(dx, dy)
					else:
						pyautogui.moveRel(dx, dy)
				if event_type == 'EVENT::TOUCH_DOWN':
					if self.click_time is not None:
						if time.time() - self.click_time <= 0.2:
							pyautogui.mouseDown()
							# print(self.drag_event_enabled)
						self.click_time = None
					
				if event_type == 'EVENT::TOUCH_UP_':
					pyautogui.click()
					self.click_time = time.time()
					self.drag_event_enabled = False
					self.moved = False
					
				if event_type == 'EVENT::TOUCH_UP':
					pass
				if event_type == 'EVENT::DRAG_WINDOW':
					self.drag_event_enabled = True
				if event_type == 'EVENT::TOUCH_HOLD':
					pyautogui.click(button='right')
			self.ret_data = ''

	def writable(self):
		return False  # len(self.data) > 0 and self.ip_address != ''


def socket_walk(sock1, sock2):
	# print(sock1, sock2)
	while True:
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
			try:
				s2.handle_read()
			except:
				s2.handle_close()

d = DataTransferSocket()
k = KeepAliveSocket(d)
socket_walk(d, k)

