import sys
import os
from pprint import pprint

sys.path.append("./build/pynui")
from pynui import Nui

from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task

image_path = "/Users/max/Pictures/iPhoto Library/Originals/2011/Parque Lecocq/"
 
class MyApp(ShowBase):
  def __init__(self):
    ShowBase.__init__(self)

    self.nui = Nui()
    self.taskMgr.add(self.nuiTask, "NuiTask")
    
    files = [image_path + f for f in os.listdir(image_path)]
    files.sort()

    self.win.setClearColor(VBase4(0, 0, 0, 0))

    self.cam.setPos(0, -2, 0)
    self.camLens.setFov(90)
    self.camLens.setNear(0.01)
    self.camLens.setFar(1000)
    
    maker = CardMaker("")
    maker.setFrameFullscreenQuad()
    card = NodePath(maker.generate())
    card.reparentTo(render)

    texture = loader.loadTexture(files[0])
    card.setTexture(texture)

    def printusers():
      pprint(self.nui.users)
    self.accept("u", printusers)

  def nuiTask(self, task):
    self.nui.update()
    users = self.nui.users
    return Task.cont
 
app = MyApp()
app.run()
