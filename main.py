import sys
import os
from pprint import pprint
from math import *

sys.path.append("./build/pynui")
from pynui import *

from TouchCanvas import *

from panda3d.core import *
from direct.interval.MetaInterval import Sequence
from direct.showbase.ShowBase import ShowBase
from direct.task import Task

class Bezier:
  def __init__(self, p1, t1, p2, t2):
    self.p = [p1, p1 + t1, p2 + t2, p2]

  def __getitem__(self, t):
    _t = 1 - t
    _t2 = _t*_t
    _t3 = _t2*_t
    t2 = t*t
    t3 = t2*t
    return self.p[0]*_t3 + self.p[1]*(3*_t2*t) + self.p[2]*(3*_t*t2) + self.p[3]*t3

class App(ShowBase):
  image_path = "/Users/max/Pictures/iPhoto Library/Originals/2011/Parque Lecocq/"
  pic_stride = 2.05
  
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
    files = sorted([App.image_path + f for f in os.listdir(App.image_path)])[0:3]
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
      left += App.pic_stride
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

  def interpolateTask(self, task, interpolator, time):
    a = min(1, task.time/time)
    self.picsNode.setPos(interpolator[a], 0, 0)
    return Task.cont if a < 1 else Task.done

  def touch_down(self, touch):
    self.taskMgr.remove("interpolateTask")
    if self.current_touch is None:
      self.current_touch = touch

  def touch_move(self, touch):
    if touch != self.current_touch:
      return
    if len(touch.smooth_positions) > 1:
      delta = touch.smooth_positions[-1].x - touch.smooth_positions[-2].x
      self.picsNode.setPos(self.picsNode.getPos().x + delta, 0, 0)

  def touch_up(self, touch):
    if touch == self.current_touch:
      self.current_touch = self.touch_canvas.touches[0] if self.touch_canvas.touches else None
    if not self.current_touch:
      task = PythonTask(self.interpolateTask)
      start = self.picsNode.getPos().x
      speed = touch.smooth_speeds[-1].x
      target_index = floor(-start / App.pic_stride + 0.5)
      if fabs(speed) > 1.5: target_index += 1 if speed < 0 else -1
      target_index = max(0, min(self.picsNode.getNumChildren()-1, target_index))
      target = -target_index * App.pic_stride
      interpolator = Bezier(start, min(speed, 1.5), target, 0)
      self.taskMgr.add(task, "interpolateTask", 0, [task, interpolator, 0.5])

if __name__ == '__main__':
  app = App()
  app.run()
