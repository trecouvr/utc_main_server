# -*- coding: utf-8 -*-
"""
@author Thomas

Récupère les infos du protocole.h, comme ça pas besoin d'éditer 2 fichiers
"""


import os
ROOT_DIR  = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]

import re


class KillException(Exception):
	def __init__(self, msg = ""):
		Exception.__init__(self, "KillException : %s"%msg)

class TimeoutException(Exception):
	def __init__(self, msg = ""):
		Exception.__init__(self, "Timeout : %s"%msg)


f = open(os.path.join(ROOT_DIR,"com","protocole.h"))
for line in f:
	t = re.search('(?<=#define)\s+(?P<var>\w+)(\s|=)+[\'"](?P<value>[^\s|\/]+)[\'"]', line)
	if t:
		locals()[t.group('var')] = t.group('value')
		if __name__ == "__main__": print t.group('var'),"\t= (str)",t.group('value')
	else:
		t = re.search('(?<=#define)\s+(?P<var>\w+)(\s|=)+(?P<value>[^\s|\/]+)', line)
		if t:
			try:
				value = int(t.group('value'))
			except:
				value = None
			locals()[t.group('var')] = value
			if __name__ == "__main__": print t.group('var'),"\t= (int)",value
f.close()


if __name__ == "__main__":
	print ROOT_DIR
