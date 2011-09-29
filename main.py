import sys
import os
from pprint import pprint
from math import *
from time import clock

sys.path.append("./build/pynui")
from pynui import *

from TouchCanvas import *

from panda3d.core import *
from direct.interval.MetaInterval import Sequence
from direct.showbase.ShowBase import ShowBase
from direct.task import Task

class CubicInterpolator:
  def __init__(self, p0, p1, v0):
    self.a = -2*p1 + v0 + 2*p0
    self.b = p1 - self.a - v0 - p0
    self.c = v0
    self.d = p0
    
  def __call__(self, t):
    t2 = t*t
    t3 = t2*t
    return self.a * t3 + self.b * t2 + self.c * t + self.d

class Hand:
  def __init__(self, app):
    y = -0.01
    size = 0.06
    maker = CardMaker("")
    maker.setFrame(
      Point3(0, y, 0),
      Point3(size, y, 0),
      Point3(size, y, size),
      Point3(0, y, size))

    def texture(file):
      t = loader.loadTexture(file)
      t.setWrapU(Texture.WMBorderColor)
      t.setWrapV(Texture.WMBorderColor)
      t.setBorderColor(VBase4())
      return t
    self.texture = texture("resources/hand.png")
    self.drag_texture = texture("resources/hand-drag.png")

    self.node = NodePath(maker.generate())
    self.node.setTexture(self.texture)
    self.node.setPos(0, 0, -2)
    self.node.setTransparency(TransparencyAttrib.MAlpha, 1)
    self.node.setTwoSided(True)
    self.node.reparentTo(app.render)

  def set_side(self, side):
    self.node.setScale(1 if side == Skeleton.right else -1, 1, 1)

  def set_drag(self, drag):
    self.node.setTexture(self.drag_texture if drag else self.texture)

class App(ShowBase):
  image_path = "images/"
  pic_stride = 2.05
  
  def __init__(self):
    ShowBase.__init__(self)

    loadPrcFile("local-config.prc")
    base.disableMouse()

    self.win.setClearColor(VBase4(0, 0, 0, 0))
    wp = WindowProperties()
    wp.setSize(1366, 768)
    base.win.requestProperties(wp)

    self.nui = Nui()
    self.nui.smooth_factor = 0.8
    self.taskMgr.add(self.nuiTask, "NuiTask")

    self.cam.setPos(0, -1, 0)
    self.camLens.setFov(90)
    self.camLens.setNear(0.01)
    self.camLens.setFar(2)

    self.picsNode = render.attachNewNode("Pics Node")

    maker = CardMaker("")
    frameRatio = wp.getXSize() / wp.getYSize()
    left = 0
    files = [App.image_path + f for f in os.listdir(App.image_path)]
    before = clock()
    print "Loading", len(files), "files..."
    for file in files:
      try:
        texture = loader.loadTexture(file, minFilter=Texture.FTLinearMipmapLinear)
      except:
        continue
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
    print "Loaded in", str(clock() - before) + "s"

    self.hand = Hand(self)
    
    self.current_touch = None
    self.touch_canvas = TouchCanvas()
    self.touch_canvas.touch_down = self.touch_down
    self.touch_canvas.touch_move = self.touch_move
    self.touch_canvas.touch_up = self.touch_up
    self.touch_canvas.cursor_move = self.cursor_move

  def nuiTask(self, task):
    self.nui.update()
    self.touch_canvas.update(self.nui.users)
    return Task.cont

  def interpolateTask(self, task, interpolator, time):
    a = min(1, task.time/time)
    self.picsNode.setPos(interpolator(a), 0, 0)
    return Task.cont if a < 1 else Task.done

  def cursor_move(self, pos, user, side):
    self.hand.set_side(side)
    z = min(0, max(-0.2, -pos.z*2))
    self.hand.node.setPos(pos.x, z, pos.y)

  def touch_down(self, touch):
    self.taskMgr.remove("interpolateTask")
    if self.current_touch is None and touch.user_side == self.touch_canvas.cursor:
      self.current_touch = touch
      self.hand.set_drag(True)

  def touch_move(self, touch):
    if touch != self.current_touch: return
    if len(touch.positions) > 1:
      delta = touch.positions[-1].x - touch.positions[-2].x
      self.picsNode.setPos(self.picsNode.getPos().x + delta, 0, 0)

  def index_for_position(self, pos):
    return floor(-pos / App.pic_stride + 0.5)
    
  def touch_up(self, touch):
    if touch != self.current_touch: return

    touches = [t for t in self.touch_canvas.touches.values() if t.user_side == self.touch_canvas.cursor]
    self.current_touch = touches[0] if touches else None

    if not self.current_touch:
      self.hand.set_drag(False)
      task = PythonTask(self.interpolateTask)
      start = self.picsNode.getPos().x
      speed = touch.speeds[-1].x
      target_index = self.index_for_position(start)
      delta = touch.positions[-1].x - touch.positions[0].x
      if fabs(speed) > 2 and target_index == self.index_for_position(start - delta):
        target_index += 1 if speed < 0 else -1
      speed = min(fabs(speed), 8) * (1 if speed > 0 else -1)
      target_index = max(0, min(self.picsNode.getNumChildren()-1, target_index))
      target = -target_index * App.pic_stride
      interp = CubicInterpolator(start, target, speed)
      self.taskMgr.add(task, "interpolateTask", 0, [task, interp, 0.5])

if __name__ == '__main__':
  app = App()
  app.run()
