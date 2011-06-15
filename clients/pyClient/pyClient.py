# -*- coding: utf-8 -*-

import socket
import threading
import sys

class pyClient:
	""" @author Thomas
		
	classe python de base pour communiquer avec le serveur
	"""
	
	def __init__(self, host, port, fn_output, fn_input=None, fn_on_close=None):
		"""
		@param host ip dus erveur
		@param port port sur lequel écouter
		@param fn_input fonction qui doit renvoyer les données à envoyer
		"""
		self._fn_output = fn_output
		self._fn_input = fn_input
		self._fn_on_close = fn_on_close
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._socket.settimeout(1.0)
		self._socket.connect((host, port))
		self._e_close = threading.Event()
		self._lock_write = threading.Lock()
	
	def start(self):
		self.t_send = threading.Thread(None, self._fn_send, None)
		self.t_recv = threading.Thread(None, self._fn_recv, None)
		self.t_send.start()
		self.t_recv.start()
		self._write("Standby ready !")

	def _fn_send(self):
		""" 
		Envoie le message récupéré par self._fn_input() au serveur
		"""
		while not self._e_close.isSet():
			if self._fn_input:
				msg = self._fn_input()
				self._socket.send(msg.strip()+"\n")
				if msg == 'close':
					self._e_close.set()
					self._write("break send")
			else:
				self._e_close.wait(1)
	
	def _fn_recv(self):
		""" 
		Récupère ce qu'envoie le serveur
		"""
		while not self._e_close.isSet():
			try:
				data = self._socket.recv(1024) # en octets/chars
			except socket.timeout:
				pass
			else:
				if not data or str(data) == 'close':
					self._socket.close()
					if self._fn_on_close : self._fn_on_close()
					self._e_close.set()
					self._write("break recv")
				self._write("Received : %s"%data)

	def _write(self, msg):
		self._lock_write.acquire()
		try:
			self._fn_output(msg.strip()+"\n")
		finally:
			self._lock_write.release()
		
