#!/usr/bin/env python

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
# This is the rio de hola client for FIFE.

from __future__ import division
from threading import Thread
import sys, os, json, urllib, urllib2
import getpass

fife_path = os.path.join('..','..','engine','python')
fife_path = os.path.join('/home','federico','tmp','sdproject','engine','python')
print "Importing fife from: "
print fife_path
if os.path.isdir(fife_path) and fife_path not in sys.path:
    sys.path.insert(0,fife_path)

from fife import fife
print "Using the FIFE python module found here: ", os.path.dirname(fife.__file__)

from fife.extensions import *
from code import world
from code.common import eventlistenerbase
from fife.extensions import pychan
from fife.extensions.pychan.pychanbasicapplication import PychanApplicationBase
from fife.extensions.pychan.fife_pychansettings import FifePychanSettings
from fife.extensions.fife_utils import getUserDataDirectory

import datetime

TDS = FifePychanSettings(app_name="rio_de_hola")

class ApplicationListener(eventlistenerbase.EventListenerBase):
    def __init__(self, engine, world):
        super(ApplicationListener, self).__init__(engine,regKeys=True,regCmd=True, regMouse=False, regConsole=False, regWidget=True)
#        super(ApplicationListener, self).__init__(engine,regKeys=True,regCmd=True, regMouse=True, regConsole=False, regWidget=True)
        self.engine = engine
        self.world = world
        self.world.gui = self
        engine.getEventManager().setNonConsumableKeys([fife.Key.ESCAPE,])
        
        self.startTime = datetime.datetime.now()

        self.quit = False
        self.window = None
        self.youLooseWindow = None
        self.youWinWindow = None

        self.rootpanel = pychan.loadXML('gui/xml/rootpanel.xml')
        self.rootpanel.mapEvents({ 
            'quitButton' : self.onQuitButtonPress,
            'aboutButton' : self.onAboutButtonPress,
            'optionsButton' : TDS.showSettingsDialog,
            'scoresButton' : self.onScoresButtonPress,
            'soundButton' : self.onSoundButtonPress
        })
        button =  self.rootpanel.getNamedChildren()['soundButton'][0]
        if int(TDS.get("FIFE", "PlaySounds")):
            button.text = unicode("Music:  ON", "utf-8")
        else:
            button.text = unicode("Music: OFF", "utf-8")
        self.rootpanel.show()

        self.character_gui = pychan.loadXML('gui/xml/player.xml')
        self.character_gui.mapEvents({ 
             'boy' : self.onBoyButtonPress,
             'girl' : self.onGirlButtonPress
         })
        self.boyButton =  self.character_gui.getNamedChildren()['boy'][0]
        self.girlButton =  self.character_gui.getNamedChildren()['girl'][0]
        self.character_gui.show()
        self.girlButton.hide()

        self.itemsContainer = pychan.loadXML('gui/xml/items.xml')
        self.itemsImages = []
        self.itemsImages.append(self.itemsContainer.getNamedChildren()['flask'][0])
        self.itemsImages.append(self.itemsContainer.getNamedChildren()['coins1'][0])
        self.itemsImages.append(self.itemsContainer.getNamedChildren()['coins2'][0])
        self.itemsImages.append(self.itemsContainer.getNamedChildren()['coins3'][0])
        #self.itemsImages.append(self.itemsContainer.getNamedChildren()['coins3'][0])
        self.itemsContainer.show()
        #for x in self.itemsImages:
        #    x.hide()
        
        # Adjust healthBar position based on resolution
        self.healthBar = pychan.loadXML('gui/xml/life.xml')
        self.healthImage = self.healthBar.getNamedChildren()['fg'][0]
        self.healthBar.show()
        size = TDS.get("FIFE", "ScreenResolution")
        self.healthBar.x = int(size.split('x')[0]) - 266 - 5
        
        # wakes up heroku server
        req_time = datetime.datetime.now()
        def callback(r):
            resp_time = datetime.datetime.now()
            print "Server up in %s seconds\n"%(str(resp_time-req_time)[5:11])
        asyncDownloadScore(callback)
    
    def girlLifeUpdate(self, life):
        length = 199/100*life
        self.healthImage.width = int(length)
    
    def keyPressed(self, evt):
        if self.world.girl.dead:
            return
        keyval = evt.getKey().getValue()
        keystr = evt.getKey().getAsString().lower()
        if keyval == fife.Key.ESCAPE:
            self.quit = True
            evt.consume()
        elif keystr == 'p':
            self.engine.getRenderBackend().captureScreen('screenshot.png')
            evt.consume()
        elif keystr == 'x':
            if self.world.mainAgent.agent.getObject().getId() == 'girl':
                self.onGirlButtonPress()
            elif self.world.mainAgent.agent.getObject().getId() == 'boy':
                self.onBoyButtonPress()
            evt.consume()

    def onCommand(self, command):
        if command.getCommandType() == fife.CMD_QUIT_GAME:
            self.quit = True
            command.consume()

    def showItems(self, items):
        for n in items:
            self.itemsImages[n].show()

    def hideItems(self, items):
        for n in items:
            self.itemsImages[n].hide()

    def youLoose(self):
        if not self.youLooseWindow:
            self.youLooseWindow = pychan.loadXML('gui/xml/youLoose.xml')
            def restartWorld():
                self.world.restart()
                self.startTime = datetime.datetime.now()
                self.girlLifeUpdate(100)
                self.youLooseWindow.hide()
            self.youLooseWindow.mapEvents({ 'closeButton' : restartWorld })
            self.youLooseWindow.distributeData({ 'looseText' : "The girl got killed. You loose. Try again!" })
        self.youLooseWindow.show()
        
    def youWin(self):
        self.youWinWindow = pychan.loadXML('gui/xml/youWin.xml')
        self.world.girl.dead = True  # stop the game
        field = self.youWinWindow.getNamedChildren()['playerField'][0]

        def restartWorld(response):
            self.world.restart()
            self.girlLifeUpdate(100)
            self.youWinWindow.hide()

        def  buttonPress():
            self.youWinWindow.distributeData({ 'winText' : "Storing data... please wait" })
            asyncSaveScore(restartWorld, {'name':field.getData(), 'time': str(end - self.startTime.replace(microsecond=0))}) 
            
        end = datetime.datetime.now().replace(microsecond=0)
        field.setData(getpass.getuser())
        self.youWinWindow.mapEvents({ 'closeButton' : buttonPress})
        self.youWinWindow.distributeData({ 'timeText' : "Elapsed time: " + str(end - self.startTime.replace(microsecond=0))})
        self.youWinWindow.show()
        
    def onQuitButtonPress(self):
        cmd = fife.Command()
        cmd.setSource(None)
        cmd.setCommandType(fife.CMD_QUIT_GAME)
        self.engine.getEventManager().dispatchCommand(cmd)

    def onAboutButtonPress(self):
        #self.youWin() # TODO FIXME XXX remove
        if not self.window:
            self.window = pychan.loadXML('gui/xml/help.xml')
            self.window.mapEvents({ 'closeButton' : self.window.hide })
            self.window.distributeData({ 'helpText' : open("misc/infotext.txt").read() })
        self.window.show()
    
    def onScoresButtonPress(self):
        if self.window:
            self.window.show()
            return
        
        def callback(response):
            out = "From http://fede-softdev.herokuapp.com/\n\n"
            for record in response:
                out += "%s won in %s in date %s\n"%(record['name'], record['time'][2:], record['date'])
            self.window.distributeData({ 'scoresText' : out })
            self.window.getNamedChildren()['scoresText'][0].adaptLayout()
            
        def refresh():
            self.window.distributeData({ 'scoresText' : "Loading..."})
            asyncDownloadScore(callback)
            
        self.window = pychan.loadXML('gui/xml/scores.xml')
        self.window.mapEvents({ 'refreshButton' : refresh})
        self.window.mapEvents({ 'closeButton' : self.window.hide })
        #self.window.distributeData({ 'helpText' : open("misc/infotext.txt").read() })
        self.window.distributeData({ 'scoresText' : "Loading..."})
        asyncDownloadScore(callback) 
        self.window.show()

    def onSoundButtonPress(self):
        button =  self.rootpanel.getNamedChildren()['soundButton'][0]
        if (self.world.soundActive == True):
            self.world.music.stop()
            self.world.soundActive = False
            button.text = unicode("Music: OFF", "utf-8")
            TDS.set("FIFE", "PlaySounds", False)
            TDS.saveSettings()
        else:
            self.world.music.play()
            self.world.soundActive = True
            button.text = unicode("Music:  ON", "utf-8")
            TDS.set("FIFE", "PlaySounds", True)
            TDS.saveSettings()

    def onBoyButtonPress(self):
        self.girlButton.show()
        self.boyButton.hide()
        self.world.switchMainAgentTo('girl')
        
    def onGirlButtonPress(self):
        self.boyButton.show()
        self.girlButton.hide()
        self.world.switchMainAgentTo('boy')



class IslandDemo(PychanApplicationBase):
    def __init__(self):
        super(IslandDemo,self).__init__(TDS)
        self.world = world.World(self.engine)
        self.listener = ApplicationListener(self.engine, self.world)
        self.world.load(str(TDS.get("rio", "MapFile"))) # Create world and agents

    def createListener(self):
        pass # already created in constructor

    def _pump(self):
        if self.listener.quit:
            self.breakRequested = True
            
            # get the correct directory to save the map file to
            mapSaveDir = getUserDataDirectory("fife", "rio_de_hola") + "/maps"
            
            # create the directory structure if it does not exist
            if not os.path.isdir(mapSaveDir):
                os.makedirs(mapSaveDir)
            
            # save map file to directory
            self.world.save(mapSaveDir + "/savefile.xml")
        else:
            self.world.pump()

def asyncDownloadScore(callback):
    def downloadScore(): 
        url = 'http://fede-softdev.herokuapp.com'
        urlconn = urllib.urlopen(url)
        urlcontents = json.loads(urlconn.read())
        callback(urlcontents)
    thread = Thread(target = downloadScore, args = ())
    thread.start()
    #thread.join()

def asyncSaveScore(callback, data):
    def saveScore(): 
        url = 'http://fede-softdev.herokuapp.com'
        #url = 'http://localhost:5000'
        req = urllib2.Request(url, json.dumps(data), {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
        callback(response)
    thread = Thread(target = saveScore, args = ())
    thread.start()
    #thread.join()
    
def main():
    app = IslandDemo()
    app.run()

if __name__ == '__main__':
    main()
