# -*- coding: utf-8 -*-
"""
@author Thomas

Les classes représentant les différnets clients acceptés par le serveur
"""

import sys
import os
SERVER_ROOT_DIR  = os.path.split(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0])[0]
sys.path.append(SERVER_ROOT_DIR)

import threading
import socket
import time
import re
import Queue

import colorConsol
from protocole import *

class Client(threading.Thread):
	def __init__(self, server, id, name):
		threading.Thread.__init__(self, None, None, name)
		self.daemon = True
		self._server = server
		self.id = id # id du client sur le serveur
		self._mask_block_from = 0 # on ne block personne à part soit même
		self._running = False # le client tourne
		self._partialMsg = ""
		self.e_validate = threading.Event()

	def __del__(self):
		self.s.close()
		print "%s destroy"%self.name()
		
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
			try:
				self._fn_send(msg)
			except Exception as ex:
				self._server.write(ex, colorConsol.FAIL)
				if self.id != ID_SERVER: self.stop()
	
	def run(self):
		"""
		Point d'entrée, envoie au client son id puis lance self._loop() en boucle
		"""
		self._server.write("%s start"%self.name(), colorConsol.OKGREEN)
		self._running = True
		while self._running and not self._server.e_shutdown.isSet():
			self._loopRecv()
		self._server.write("%s arreté"%self.name(), colorConsol.WARNING)

	def combineWithPartial(self, msg):
		"""
		Cette fonction sert à former des messages complets à partir de morceaux,
		quand on reçoit des informations via TCP on est jamais assuré d'avoir la ligne entière du premier coup
		
		@return [] si le message ne peut pas etre exploité (pas de \n à la fin)
		@return [m1,m2,m3, ...] sinon
		"""
		#print (self._partialMsg,msg)
		msg = self._partialMsg + msg
		index = msg.rfind('\n')
		if index < 0:
			self._partialMsg = msg
			#print self._partialMsg,[]
			return []
		else:
			self._partialMsg = msg[index+1:]
			#print self._partialMsg,[ m for m in msg[:index].split('\n') ]
			return [ m for m in msg[:index].split('\n') ]
	
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

	def __repr__(self):
		return self.name()
	
	
class TCPClient(Client):
	"""
	Client TCP
	"""
	def __init__(self, server, id, s, addr):
		"""
		@param server le server
		@param id id du client
		@param s socket pour écouter envoyer
		"""
		Client.__init__(self, server, id, "TCPClient(addr=%s)"%(addr,))
		self.addr = addr
		self.s = s
		self.s.settimeout(1.0) # timeout

	def name(self):
		return "TCPClient(%s,addr=%s)"%(self.id,self.addr)
		
	def _fn_send(self, msg):
		self.s.send(str(msg).strip()+"\n")
		
	def _loopRecv(self):
		msg = ""
		try:
			msg = self.s.recv(1024)
		except socket.timeout:
			pass
		except socket.error as er:
			self._server.write(self.name()+" "+str(er), colorConsol.FAIL)
		else:
			for msg in self.combineWithPartial(msg):
				self._server.write("Received from %s : '%s'"%(self.name(),msg))
				if msg:
					self._server.parseMsg(self.id, msg)	
	
class LocalClient(Client):
	"""
	Le client qui est dans le terminal lancé par main.py
	"""
	def __init__(self, server, id):
		Client.__init__(self, server, id, "LocalClient(%s)"%id)
		self.mask_recv_from = -1
		self.macros = {}
		self._queue = Queue.Queue()

	def name(self):
		return "LocalClient(%s)"%(self.id)
	
	def _fn_send(self, msg):
		self._queue.put(msg)
		"""
		self._server.write("Received on server : '%s'"%msg)
		id_from, msg = msg.strip().split(C_SEP_SEND,1)
		id_from = int(id_from)
		if "sd" == msg:
			self._server.shutdown()
		else:
			try:
				msg_split = msg.split('.')
				try:
					id_msg = int(msg_split[0])
					id_cmd = int(msg_split[1])
				except ValueError as ex:
					pass
				else:
					if id_msg == -999: # la demande d'identification du début
						if id_from != int(msg_split[1]):
							for client in self._server.clients:
								if client.id == id_from:
									client.id = int(msg_split[1])
									if client.id == ID_IA:
										client.mask_recv_from = (-1 ^ (1 << self.id)) # tout le monde sauf soit meme	
									client.e_validate.set()
					elif id_cmd == Q_KILL: # arret du robot
						for client in self._server.clients:
							if client.id != ID_SERVER and client.id != ID_IA:
								print client
								client.stop()
							
			except Exception as ex:
				self._server.write("ERROR : LocalClient, execute commande '%s'"%ex, colorConsol.FAIL)
			
			# lister les clients
			if "ls" == msg:
				for client in self._server.clients:
					self._server.write(client, colorConsol.OKBLUE)
			
			# loop
			t = re.match('loop\(([^\),]+),([^\),]+),([^\),]+)\).*',msg)
			if t:
				try:
					nb_iter = int(t.group(1))
					interval = int(t.group(2))
					cmd = t.group(3)
				except IndexError:
					self.write("ERROR : manque de paramètres, signature de la fonction : loop(nb_iter,interval,cmd)", colorConsol.FAIL)
				else:
					start = time.time()
					for i in xrange(nb_iter):
						self._server.parseMsg(self.id, cmd)
						time.sleep(float(interval)/1000.0)
					self._server.write("Temps exec loop : %sms"%(time.time()-start), colorConsol.OKBLUE)
					
			# créer une macro
			t = re.match('mac\(([^\),]+),([^\),]+)\).*',msg)
			if t:
				try:
					macro = t.group(1)
					cmd = t.group(2)
				except IndexError:
					self.write("ERROR : manque de paramètres, signature de la fonction : mac(macro,cmd)", colorConsol.FAIL)
				else:
					self.macros[macro] = cmd
					self._server.write("macro '%s' is for commande '%s'"%(cmd,macro), colorConsol.OKGREEN)

			# macros
			if msg in self.macros:
				self._server.parseMsg(self.id, self.macros[msg])
		"""
					
	def _loopRecv(self):
		msg = self._queue.get()
		self._server.write("Received on server : '%s'"%msg)
		msg_split = str(msg).split(C_SEP_SEND)
		id_from = int(msg_split[0])
		if len(msg_split) > 1:
			# commande interne
			t = re.match('(?P<cmd>\w+)\((?P<params>.*)\)',msg_split[1])
			if t:
				cmd = t.group('cmd')
				cmd = cmd.lower()
				params = t.group('params')
				params = params.strip().split(',')
				self.cmdIntern(cmd, *params)
			# appel d'une macro
			if msg_split[1] in self.macros:
				self._server.parseMsg(self.id, self.macros[msg_split[1]])
		self._queue.task_done()

	def cmdIntern(self,cmd, *params):
		if cmd == 'macro':
			self.addMacro(*params)
		elif cmd == 'sd':
			self.shutdownServer()
		elif cmd == 'ls':
			self.listClients()
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
		self._server.write(reduce(lambda x,y: str(x) + str(y),self._server.clients), colorConsol.OKBLUE)
		
	def shutdownServer(self):
		self._server.shutdown()	
		
class SerialClient(Client):
	"""
	connection aux cartes arduinos
	"""
	def __init__(self, server, id, serial, port, baudrate):
		Client.__init__(self, server, id, "SerialClient(port=%s,baudrate=%s)"%(port,baudrate))
		self.serial = serial
		self.port = port
		self.baudrate = baudrate
	
	def name(self):
		return "SerialClient(%s,port=%s,baudrate=%s)"%(self.id,self.port,self.baudrate)
	
	def _fn_send(self, msg):
		self.serial.write(str(msg).strip()+"\n")
		
	def _loopRecv(self):
		msg = self.serial.readline()
		if msg:
			for msg in self.combineWithPartial(msg):
				self._server.write("Received from %s : '%s'"%(self.name(),msg))
				self._server.parseMsg(self.id, msg)

	def stop(self):
		self.serial.close()
		Client.stop(self)

class SubprocessClient(Client):
	def __init__(self, server, id, process, exec_name):
		Client.__init__(self, server, id, "SubprocessClient(exc_name=%s)"%(exec_name))
		self.process = process
		self.exec_name = exec_name

	def name(self):
		return "SubprocessClient(%s,exc_name=%s)"%(self.id,self.exec_name)
		
	def _fn_send(self, msg):
		self._server.write("send to subprocess(%s) '%s'"%(self.name(),str(msg).strip()+"\n"))
		self.process.stdin.write(str(msg).strip()+"\n") # envoie au child
		self.process.stdin.flush()
	
	def _loopRecv(self):
		msg = self.process.stdout.readline()
		if msg:
			for msg in self.combineWithPartial(msg):
				self._server.write("Received from %s : '%s'"%(self.name(),msg))
				self._server.parseMsg(self.id, msg)
	
	def stop(self):
		self.process.kill()
		Client.stop(self)


