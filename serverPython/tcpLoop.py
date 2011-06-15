# -*- coding: utf-8 -*-
"""
@author Thomas

Le thread écoutant les connection TCP entrantes pour ensuite les transformer en clients
"""
import client
import threading
import socket
import colorConsol


class TCPLoop(threading.Thread):
	"""
	Class qui va écouter les connections entrantes sur un socket
	"""
	def __init__(self, server, host, port):
		"""
		@param server le serveur
		"""
		threading.Thread.__init__(self, None, None, "TCPLoop(%s,%s)"%(host,port))
		self.daemon = True
		self._server = server
		self._host = host
		self._port = port
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._socket.settimeout(1.0)
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._socket.bind((host, port))
		self._socket.listen(1)
	
	def __del__(self):
		self._socket.close()
		self._server.write("TCPLoop(%s,%s) destroy"%(self._host,self._port), colorConsol.WARNING)
	
	def run(self):
		self._server.write("TCPLoop(%s,%s) start"%(self._host,self._port), colorConsol.OKGREEN)
		while not self._server.e_shutdown.isSet():
			self._loop()
		self._server.write("TCPLoop(%s,%s) arreté"%(self._host,self._port), colorConsol.WARNING)
	
	def _loop(self):
		try:
			conn, addr = self._socket.accept()
		except socket.timeout:
			pass
		else:
			self._server.addTCPClient(conn, addr)
	
	
	
