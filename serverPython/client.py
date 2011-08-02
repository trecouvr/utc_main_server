# -*- coding: utf-8 -*-
"""
@author Thomas

Les classes représentant les différnets clients acceptés par le serveur
"""

import sys
import os
SERVER_ROOT_DIR  = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
sys.path.append(SERVER_ROOT_DIR)
sys.path.append(os.path.join(SERVER_ROOT_DIR,"serverPython"))

import threading
import socket
import time
import re
import queue
import traceback
from functools import reduce

from protocole import *
import colorConsol

class BasicClient(threading.Thread):
	def __init__(self, threadname, fn_write=None):
		threading.Thread.__init__(self, None, None, threadname)
		if fn_write:
			self._fn_write = fn_write
		else:
			self._fn_write = sys.stdout.write
		self.daemon = True
		self._running = False # le client tourne
		self._partialMsg = ""
		self._lock_send = threading.Lock()

	def send(self, msg):
		self._lock_send.acquire()
		try:
			self._fn_send(msg)
		except Exception as ex:
			self._fn_write("\n".join(traceback.extract_tb(sys.exc_info()[2])) + "\n" + str(ex), colorConsol.FAIL)
		finally:
			self._lock_send.release()
	
	def run(self):
		"""
		Point d'entrée, envoie au client son id puis lance self._loop() en boucle
		"""
		self._fn_write("%s start"%self, colorConsol.OKGREEN)
		self._running = True
		while self._running:
			self._loopRecv()
		self._fn_write("%s arreté"%self, colorConsol.WARNING)
		
	def stop(self):
		self._running = False

	def _fn_loopRecv(self):
		""" Must be override """
		raise Exception("_fn_loopRecv doit être surchargé")

	def _fn_send(self):
		""" Must be override """
		raise Exception("_fn_on_msg_recv doit être surchargé")
	
	def combineWithPartial(self, msg):
		"""
		Cette fonction sert à former des messages complets à partir de morceaux,
		quand on reçoit des informations via TCP on est jamais assuré d'avoir la ligne entière du premier coup
		
		@return [] si le message ne peut pas etre exploité (pas de \n à la fin)
		@return [m1,m2,m3, ...] sinon
		"""
		#print (self._partialMsg,msg)
		msg = self._partialMsg + str(msg,"utf-8")
		index = msg.rfind('\n')
		if index < 0:
			self._partialMsg = msg
			#print self._partialMsg,[]
			return []
		else:
			self._partialMsg = msg[index+1:]
			#print self._partialMsg,[ m for m in msg[:index].split('\n') ]
			return [ m for m in msg[:index].split('\n') ]
	
	def __del__(self):
		self._fn_write("%s destroy"%self)

	def __repr__(self):
		return "BasicClient"
		
class ServerClient(BasicClient):
	def __init__(self, server, id, name):
		BasicClient.__init__(self, name, server.write)
		self._server = server
		self.id = id # id du client sur le serveur
		self._mask_block_from = 0 # on ne block personne à part soit même

	def __del__(self):
		self._fn_write("%s destroy"%self)
		
	def stop(self):
		self._running = False
		
	def send(self, mask_from, msg):
		"""
		@param mask_from id du client qui a envoyé le message
		@param msg message à envoyer
		"""
		if self._mask_block_from & mask_from:
			#self._server.write("client with mask '%s' is not authorized to send to client #%s"%(mask_from,self.id), colorConsol.WARNING)
			pass
		else:
			#self._server.write("send to %s, %s"%(self.id,msg))
			BasicClient.send(self,msg)
	
	def blockFrom(self, id_client):
		"""
		Bloque l'écoute sur un client choisit
		
		@param id_client (in) id du client choisit
		"""
		self._mask_block_from |= (1 << id_client)

	def allowFrom(self, id_client):
		"""
		Authorise un client à nous parler

		@param id_client (int) id du client choisit
		"""
		self._mask_block_from &= ~(1 << id_client)
		
	
	def blockAll(self):
		"""
		Le client ne reçoit plus de messages
		"""
		self._mask_block_from = -1

	def allowAll(self):
		"""
		Ecoute de tout le monde
		"""
		self._mask_block_from = -1
	
	
class TCPClient(ServerClient):
	"""
	Client TCP
	"""
	def __init__(self, server, id, s, addr):
		"""
		@param server le server
		@param id id du client
		@param s socket pour écouter envoyer
		"""
		ServerClient.__init__(self, server, id, "TCPClient(addr=%s)"%(addr,))
		self.addr = addr
		self.s = s
		self.s.settimeout(1.0) # timeout
		
	def _fn_send(self, msg):
		self.s.send(bytes(str(msg).strip()+"\n","utf-8"))
		
	def _loopRecv(self):
		msg = ""
		try:
			msg = self.s.recv(1024)
		except socket.timeout:
			pass
		except socket.error as er:
			self._server.write(str(self)+" "+str(er), colorConsol.FAIL)
		else:
			for msg in self.combineWithPartial(msg):
				self._server.write("Received from %s : '%s'"%(self,msg))
				if msg:
					self._server.parseMsg(self.id, msg)

	def __repr__(self):
		return "TCPClient(%s,addr=%s)"%(self.id,self.addr)
	
class LocalClient(ServerClient):
	"""
	Le client qui est dans le terminal lancé par main.py
	"""
	def __init__(self, server, id):
		ServerClient.__init__(self, server, id, "LocalClient(%s)"%id)
		self.mask_recv_from = -1
		self.macros = {}
		self._queue = queue.Queue()

	def __repr__(self):
		return "LocalClient(%s)"%(self.id)
	
	def _fn_send(self, msg):
		self._queue.put(msg)
					
	def _loopRecv(self):
		msg = self._queue.get()
		self._server.write("Received on server : '%s'"%msg)
		msg_split = str(msg).split(C_SEP_SEND,1)
		id_from = int(msg_split[0])
		if len(msg_split) > 1:
			# appel d'une macro
			if msg_split[1] in self.macros:
				self._server.parseMsg(self.id, self.macros[msg_split[1]])
			# commande interne
			else:
				t = re.match('(?P<cmd>\w+) *(?P<params>.*)',msg_split[1])
				if t:
					cmd = t.group('cmd')
					cmd = cmd.lower()
					params = t.group('params')
					params = [ _.strip() for _ in params.split(' ') ] if params else []
					self.cmdIntern(cmd, *params)
		self._queue.task_done()

	def cmdIntern(self,cmd, *params):
		if cmd == 'macro':
			self.addMacro(*params)
		elif cmd == 'sd':
			self.shutdownServer()
		elif cmd == 'ls':
			self.listClients()
		elif cmd == 'h':
			self.showHelp()
		else:
			self._server.write("ERROR : commande '%s' inconnue"%cmd, colorConsol.FAIL)

	def addMacro(self, *params):
		if len(params) != 2:
			self._server.write("ERROR : mauvais nombre de paramètres, signature de la fonction : macro(macro,cmd)", colorConsol.FAIL)
		else:
			macro = params[0]
			cmd = params[1]
			self.macros[macro] = cmd
			self._server.write("'%s' <=> '%s'"%(macro,cmd), colorConsol.OKGREEN)

	def listClients(self):
		self._server.write("\n".join(map(lambda c: str(c),self._server.clients.values())), colorConsol.OKBLUE)
		
	def shutdownServer(self):
		self._server.shutdown()

	def showHelp(self):
		self._server.write("\
			ls\tlister les clients\n\
			macro(macro, cmd)\tajouter une macro\n \
			sd\téteindre le serveur\n\
			", colorConsol.OKBLUE)
		
class SerialClient(ServerClient):
	"""
	connection aux cartes arduinos
	"""
	def __init__(self, server, id, serial, port, baudrate):
		ServerClient.__init__(self, server, id, "SerialClient(port=%s,baudrate=%s)"%(port,baudrate))
		self.serial = serial
		self.port = port
		self.baudrate = baudrate
	
	def __repr__(self):
		return "SerialClient(%s,port=%s,baudrate=%s)"%(self.id,self.port,self.baudrate)
	
	def _fn_send(self, msg):
		self.serial.write(str(msg).strip()+"\n")
		
	def _loopRecv(self):
		msg = self.serial.readline()
		if msg:
			for msg in self.combineWithPartial(msg):
				self._server.write("Received from %s : '%s'"%(self,msg))
				self._server.parseMsg(self.id, msg)

	def stop(self):
		self.serial.close()
		ServerClient.stop(self)

class SubprocessClient(ServerClient):
	def __init__(self, server, id, process, exec_name):
		ServerClient.__init__(self, server, id, "SubprocessClient(exc_name=%s)"%(exec_name))
		self.process = process
		self.exec_name = exec_name

	def __repr__(self):
		return "SubprocessClient(%s,exc_name=%s)"%(self.id,self.exec_name)
		
	def _fn_send(self, msg):
		self._server.write("send to subprocess(%s) '%s'"%(self,str(msg).strip()+"\n"))
		self.process.stdin.write(str(msg).strip()+"\n") # envoie au child
		self.process.stdin.flush()
	
	def _loopRecv(self):
		msg = self.process.stdout.readline()
		if msg:
			for msg in self.combineWithPartial(msg):
				self._server.write("Received from %s : '%s'"%(self,msg))
				self._server.parseMsg(self.id, msg)
	
	def stop(self):
		self.process.kill()
		ServerClient.stop(self)


