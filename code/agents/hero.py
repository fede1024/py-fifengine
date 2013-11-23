# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2013 by the FIFE team
#  http://www.fifengine.net
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

import random
from agent import Agent
#from fife.extensions.fife_settings import Setting
from fife.fife import Location

#TDS = Setting(app_name="rio_de_hola")

# Define constants
_STATE_NONE, _STATE_IDLE, _STATE_RUN, _STATE_KICK, _STATE_TALK = xrange(5)

class Hero(Agent):
	def __init__(self, settings, model, agentName, layer, uniqInMap=True):
		super(Hero, self).__init__(settings, model, agentName, layer, uniqInMap)
		self.state = _STATE_NONE
		self.idlecounter = 1

	def onInstanceActionFinished(self, instance, action):
		#print "Action finished: " + str(action.getId())
		self.idle()
		if action.getId() != 'stand':
			self.idlecounter = 1
		else:
			self.idlecounter += 1
		if self.idlecounter % 7 == 0:
			heroTexts = self.settings.get("rio", "boyIdleTexts")
			txtindex = random.randint(0, len(heroTexts) - 1)
			instance.say(heroTexts[txtindex], 2500)

	def onInstanceActionCancelled(self, instance, action):
		pass
	
	def start(self):
		self.idle()

	def idle(self):
		self.state = _STATE_IDLE
		self.agent.actOnce('stand')

	def run(self, location):
		self.state = _STATE_RUN
		self.agent.move('run', location, 4 * self.settings.get("rio", "TestAgentSpeed"))

	def kick(self, target):
		self.state = _STATE_KICK
		self.agent.actOnce('kick', target)

	def talk(self, target):
		self.state = _STATE_TALK
		self.idlecounter = 1
		self.agent.actOnce('talk', target)

	def moveStep(self, direction):
		location = self.agent.getLocationRef()
		coords = location.getMapCoordinates()
		rot = self.agent.getRotation()

		if direction == 'l':
			rot = (rot+45)%360
			self.agent.setRotation(rot)
		elif direction == 'r':
			rot = (rot-45)%360
			self.agent.setRotation(rot)
		elif direction == 'd':
			rot = (rot+180)%360
			self.agent.setRotation(rot)
		elif direction == 'u':
			if(0 <= rot < 23 or rot >= 338):
				coords.x += +0.5
			elif (23 <= rot < 68):
				coords.x += +0.5
				coords.y += -0.5
			elif (68 <= rot < 113):
				coords.y += -0.5
			elif (113 <= rot < 158):
				coords.x += -0.5
				coords.y += -0.5
			elif (158 <= rot < 203):
				coords.x += -0.5
			elif (203 <= rot < 248):
				coords.x += -0.5
				coords.y += +0.5
			elif (248 <= rot < 293):
				coords.y += +0.5
			elif (293 <= rot < 338):
				coords.x += +0.5
				coords.y += +0.5
			nl = Location(location)
			nl.setMapCoordinates(coords)
			self.run(nl)
