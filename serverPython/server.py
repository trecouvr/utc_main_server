# -*- coding: utf-8 -*-
"""
@author Thomas

Le Serveur python, centre du réseau, des clients Subprocess (stdin/stdout),
TCP, et Serial peuvent se connecter et échanger des informations
"""
import sys
import os
ROOT_DIR  = os.path.split(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0])[0]
sys.path.append(os.path.join(ROOT_DIR,"com"))

import random
import threading
import serial
import subprocess

from sender import *
from client import *
from tcpLoop import *
import colorConsol
from protocole import *


class Server():
	"""
	Cette classe permet la communication avec les différents ports série
	
	@author Thomas
	"""
	def __init__(self):
		self.clients = []
		self.sender = Sender(self)
		#self.tcpLoop = TCPLoop(self,'', random.randint(40000,60000))
		self.tcpLoop = TCPLoop(self,'', 50000)
		self.e_shutdown = threading.Event()
		self._lock_write = threading.Lock()
		self._lock_addClient = threading.Lock()
		
		locClient = LocalClient(self, 0)
		locClient.start()
		self.clients.append(locClient)

		self.id_non_validate = 13
		
		
	def start(self):
		self.tcpLoop.start()
		self.sender.start()
	
	def shutdown(self):
		self.e_shutdown.set()

	def _identClient(self, client):
		self.parseMsg(ID_SERVER, str(client.id)+C_SEP_SEND+'-999'+C_SEP_SEND+str(Q_IDENT)) # une identification
		client.e_validate.wait(2)
		self.write("After ident :%s"%client, colorConsol.OKGREEN)
		
	def addTCPClient(self, conn, addr):
		self._lock_addClient.acquire()
		try:
			client = TCPClient(self,self.id_non_validate, conn, addr)
			self.id_non_validate+=1
			client.start()
			self.clients.append(client)
			self._identClient(client)
		except Exception as ex:
			self.write(ex, colorConsol.FAIL)
		finally:
			self._lock_addClient.release()
			
	
	def addSerialClient(self, port, baudrate):
		self._lock_addClient.acquire()
		try:
			s = serial.Serial(port, baudrate, timeout=1, writeTimeout=1)
			client = SerialClient(self, self.id_non_validate, s, port, baudrate)
			self.id_non_validate+=1
			client.start()
			self.clients.append(client)
			time.sleep(1) # avant de pouvoir envoyer de recevoir des infos il faut attendre
			self._identClient(client)
		except Exception as ex:
			self.write(ex, colorConsol.FAIL)
		finally:
			self._lock_addClient.release()
	
	def addSubprocessClient(self, exec_name):
		self._lock_addClient.acquire()
		try:
			try:
				process = subprocess.Popen(exec_name, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			except OSError as e:
				self.write("Server->addSubprocessClient(%s) failed"%exec_name, colorConsol.FAIL)
				self.write(e, colorConsol.FAIL)
			except Exception as ex:
				self.write(ex, colorConsol.FAIL)
			else:
				client = SubprocessClient(self, self.id_non_validate, process, exec_name)
				self.id_non_validate+=1
				client.start()
				self.clients.append(client)
				self._identClient(client)
		finally:
			self._lock_addClient.release()
		
	def parseMsg(self, id_client, msg):
		"""
		parse un message avant de l'envoyer
		"""
		if msg and msg[0] not in '-0123456789':
			msg = str(ID_SERVER)+'.' + msg
		
		try:
			id_to, msg = msg.strip().split(C_SEP_SEND,1)
			id_to = int(id_to)
			mask_from = (1 << id_client)
			mask_to = -1 if id_to == -1 else (1 << id_to)
			msg = str(id_client)+C_SEP_SEND+msg
			self.sender.addMsg(mask_from, mask_to, msg)
		except ValueError as ex:
			self.write("ERROR : Server.parseMsg : %s"%msg, colorConsol.FAIL);
	
	def write(self, msg, color=None):
		self._lock_write.acquire()
		try:
			if color: print color+str(msg).strip()+colorConsol.ENDC
			else: print str(msg).strip()
		finally:
			self._lock_write.release()

