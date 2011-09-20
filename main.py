import sys
import os
from pprint import pprint

sys.path.append("./build/pynui")
from pynui import *

from TouchCanvas import *

from panda3d.core import *
from direct.interval.MetaInterval import Sequence
from direct.showbase.ShowBase import ShowBase
from direct.task import Task

image_path = "/Users/max/Pictures/iPhoto Library/Originals/2011/Parque Lecocq/"

class App(ShowBase):
  def __init__(self):
    ShowBase.__init__(self)

    self.nui = Nui()
    self.taskMgr.add(self.nuiTask, "NuiTask")

    self.win.setClearColor(VBase4(0, 0, 0, 0))

    self.setFrameRateMeter(True)
    PStatClient.connect()

    self.cam.setPos(0, -1, 0)
    self.camLens.setFov(90)
    self.camLens.setNear(0.01)
    self.camLens.setFar(1000)

    self.picsNode = render.attachNewNode("Pics Node")

    maker = CardMaker("")
    frameRatio = self.camLens.getAspectRatio()
    left = 0
    files = sorted([image_path + f for f in os.listdir(image_path)])[0:3]
    print "Loading", len(files), "files..."
    for file in files:
      texture = loader.loadTexture(file)
      texture.setMinfilter(Texture.FTLinearMipmapLinear)
      texture.setAnisotropicDegree(4)
      textureRatio = texture.getOrigFileXSize() * 1.0 / texture.getOrigFileYSize()
      scale = textureRatio/frameRatio if textureRatio < frameRatio else 1
      maker.setFrame(
        Point3(-1 * scale, 0, -1 / textureRatio * scale),
        Point3(1 * scale, 0, -1 / textureRatio * scale),
        Point3(1 * scale, 0, 1 / textureRatio * scale),
        Point3(-1 * scale, 0, 1 / textureRatio * scale))
      card = NodePath(maker.generate())
      card.reparentTo(self.picsNode)
      card.setTexture(texture)
      card.setPos(left, 0, 0)
      left += 2.05
    print "Loaded"

    self.accept("u", lambda: pprint(self.nui.users))

    self.current_touch = None
    self.touch_canvas = TouchCanvas()
    self.touch_canvas.touch_down = self.touch_down
    self.touch_canvas.touch_move = self.touch_move
    self.touch_canvas.touch_up = self.touch_up

  def nuiTask(self, task):
    self.nui.update()
    self.touch_canvas.update(self.nui.users)
    return Task.cont

  def touch_down(self, touch):
    if self.current_touch is None:
      self.current_touch = touch

  def touch_move(self, touch):
    if touch != self.current_touch:
      return
    if len(touch.smooth_positions) > 1:
      delta = touch.smooth_positions[-1] - touch.smooth_positions[-2]
      self.picsNode.setPos(self.picsNode.getPos() + Vec3(delta.x * 2, 0, 0))

  def touch_up(self, touch):
    if touch == self.current_touch:
      self.current_touch = self.touch_canvas.touches[0] if self.touch_canvas.touches else None

if __name__ == '__main__':
  app = App()
  app.run()
