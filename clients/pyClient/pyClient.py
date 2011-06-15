# -*- coding: utf-8 -*-

import os
import sys
SERVER_ROOT_DIR  = os.path.split(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0])[0]
sys.path.append(SERVER_ROOT_DIR)

import socket
import threading
import traceback
from serverPython.client import BasicClient, colorConsol

class PyClient(BasicClient):
	""" @author Thomas
		
	classe python de base pour communiquer avec le serveur
	"""
	def __init__(self, host, port, threadname="PyClient", fn_write=None):
		"""
		@param host ip dus erveur
		@param port port sur lequel écouter
		"""
		super(PyClient,self).__init__(threadname, fn_write)
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._socket.settimeout(1.0)
		self._socket.connect((host, port))
		self._running = False
		self._lock_write = threading.Lock()
		self._lock_send = threading.Lock()

	def _fn_on_msg_recv(self, msg):
		""" Must be override """
		raise Exception("_fn_on_msg_recv doit être surchargé")
	
	def _fn_send(self, msg):
		self._socket.send(str(msg).strip()+"\n")
		
	def _loopRecv(self):
		msg = ""
		try:
			msg = self._socket.recv(1024)
		except socket.timeout:
			pass
		except socket.error as er:
			self._fn_write(self+" "+str(er), colorConsol.FAIL)
		else:
			for msg in self.combineWithPartial(msg):
				self._fn_on_msg_recv(msg)
		
if __name__ == "__main__":
	print SERVER_ROOT_DIR
	lock_write = threading.Lock()
	
	def write(msg, color=None):
		lock_write.acquire()
		try:
			if color: print color+str(msg).strip()+colorConsol.ENDC
			else: print str(msg).strip()
		finally:
			lock_write.release()
	
	class MyPyClient(PyClient):
		def __init__(self, host, port):
			PyClient.__init__(self,host, port, "MyPyCLient", write)

		def _fn_on_msg_recv(self, msg):
			self._fn_write("msg reçu : %s"%msg)
	
	client = MyPyClient("localhost",50000)
	client.start()

	while True:
		msg = raw_input()
		client.send(msg)





