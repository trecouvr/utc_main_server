# -*- coding: utf-8 -*-
"""
@author Thomas

Les classes représentant les différnets clients acceptés par le serveur
"""

import sys
import os
ROOT_DIR  = os.path.split(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0])[0]
sys.path.append(os.path.join(ROOT_DIR,"com"))

import threading
import socket
import time
import re

import colorConsol
from protocole import *

class Client(threading.Thread):
	def __init__(self, server, id, name):
		threading.Thread.__init__(self, None, None, name)
		self._server = server # la socket pour envoyer recevoir
		self.id = id # id du client sur le serveur
		self._running = False # le client tourne
		self.mask_recv_from = (-1 ^ (1 << self.id)) # tout le monde sauf soit meme 
		self._partialMsg = ""
		self.e_validate = threading.Event()

		if self.id != ID_SERVER:
			self.blockRecv() # empecher toute reception
			self.setMaskRecvFrom(ID_SERVER,1) # les cartes ne peuvent recevoir des messages que du serveur
			self.setMaskRecvFrom(ID_IA,1) # et de l'IA
	
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
		if self.mask_recv_from & mask_from:
			#self._server.write("send to %s, %s"%(self.id,msg))
			try:
				self._fn_send(msg)
			except Exception as ex:
				self._server.write(ex, colorConsol.FAIL)
				if self.id != ID_SERVER: self.stop()
		else:
			#self._server.write("client with mask '%s' is not authorized to send to client #%s"%(mask_from,self.id), colorConsol.WARNING)
			pass
	
	def run(self):
		"""
		Point d'entrée, envoie au client son id puis lance self._loop() en boucle
		"""
		self._server.write("%s start"%self.name(), colorConsol.OKGREEN)
		self._running = True
		self.send(1,str(ID_SERVER)+C_SEP_SEND+str(Q_IDENT)+C_SEP_SEND+str(self.id)+"\n")
		while self._running and not self._server.e_shutdown.isSet():
			self._loopRecv()
		self._server.write("%s arreté"%self.name(), colorConsol.WARNING)

	def combineWithPartial(self, msg):
		"""
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
	
	def setMaskRecvFrom(self, id_client, b):
		"""
		set l'état d"coute du client choisit
		@param id_client le client choisit
		@param b 1 pour écouter, 0 pour ne pas écouter
		"""
		if b:
			self.mask_recv_from |= (1 << id_client)
		else:
			self.mask_recv_from &= ~(b << id_client)
	
	def blockRecv(self):
		"""
		Le client ne reçoit plus de messages
		"""
		self.mask_recv_from = 0

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
		Client.__init__(self, server, id, "LocalClient()")
		self.mask_recv_from = -1
		self.macros = {}

	def name(self):
		return "LocalClient(%s)"%(self.id)
	
	def _fn_send(self, msg):
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
					
					
	
	def _loopRecv(self):
		msg = raw_input()+"\n"
		for msg in self.combineWithPartial(msg):
			msg = msg.strip()
			self._server.parseMsg(self.id, msg)
		
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


