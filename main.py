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
    wp.setSize(1536, 768)
    base.win.requestProperties(wp)

    self.nui = Nui()
    self.nui.smooth_factor = 0.8
    self.taskMgr.add(self.nui_task, "NuiTask")

    self.cam.setPos(0, -1, 0)
    self.camLens.setFov(90)
    self.camLens.setNear(0.01)
    self.camLens.setFar(2)

    self.picsNode = render.attachNewNode("Pics Node")

    maker = CardMaker("")
    frameRatio = wp.getXSize() / wp.getYSize()
    left = 0
    files = [App.image_path + f for f in os.listdir(App.image_path)][0:5]
    before = clock()
    print "Loading", len(files), "files..."
    for file in files:
      try:
         texture = loader.loadTexture(file)
      except:
        continue
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
    print "Loaded in", str(clock() - before) + "s"

    self.hand = Hand(self)
    
    self.current_touch = None
    self.touch_canvas = TouchCanvas()
    self.touch_canvas.touch_down = self.touch_down
    self.touch_canvas.touch_move = self.touch_move
    self.touch_canvas.touch_up = self.touch_up
    self.touch_canvas.cursor_move = self.cursor_move
    self.touch_canvas.cursor_appear = self.cursor_appear
    self.touch_canvas.cursor_disappear = self.cursor_disappear
    
  def nui_task(self, task):
    self.nui.update()
    self.touch_canvas.update(self.nui.users)
    return Task.cont

  def interpolate_task(self, task, interpolator, time, axis, node):
    a = min(1, task.time/time)
    v = node.getPos()
    v.__setattr__(axis, interpolator(a))
    node.setPos(v)
    return Task.cont if a < 1 else Task.done

  def interpolate(self, name, node, axis, to, speed=0, time=0.5):
    v = node.getPos()
    interp = CubicInterpolator(v.__getattribute__(axis), to, speed)
    task = PythonTask(self.interpolate_task, name)
    self.taskMgr.add(task, extraArgs=[task, interp, time, axis, node])
    
  def cursor_appear(self):
    self.taskMgr.remove("zoom")
    offset = 0.2
    self.interpolate("zoom", self.picsNode, 'y', offset)
    vfov = radians(self.camLens.getVfov())
    self.interpolate("zoom", self.picsNode, 'z', -offset * tan(vfov/2))

  def cursor_disappear(self):
    self.taskMgr.remove("zoom")
    self.interpolate("zoom", self.picsNode, 'y', 0)
    self.interpolate("zoom", self.picsNode, 'z', 0)

  def cursor_move(self, pos, user, side):
    self.hand.set_side(side)
    z = min(0, max(-0.2, -pos.z*2))
    self.hand.node.setPos(pos.x, z, pos.y)

  def touch_down(self, touch):
    self.taskMgr.remove("inertia")
    if self.current_touch is None and touch.user_side == self.touch_canvas.cursor:
      self.current_touch = touch
      self.hand.set_drag(True)

  def touch_move(self, touch):
    if touch != self.current_touch: return
    if len(touch.positions) > 1:
      delta = touch.positions[-1].x - touch.positions[-2].x
      v = self.picsNode.getPos()
      self.picsNode.setPos(v.x + delta, v.y, v.z)

  def index_for_position(self, pos):
    return floor(-pos / App.pic_stride + 0.5)
    
  def touch_up(self, touch):
    if touch != self.current_touch: return

    touches = [t for t in self.touch_canvas.touches.values() if t.user_side == self.touch_canvas.cursor]
    self.current_touch = touches[0] if touches else None

    if not self.current_touch:
      self.hand.set_drag(False)
      start = self.picsNode.getPos().x
      speed = touch.speeds[-1].x
      target_index = self.index_for_position(start)
      delta = touch.positions[-1].x - touch.positions[0].x
      if fabs(speed) > 2 and target_index == self.index_for_position(start - delta):
        target_index += 1 if speed < 0 else -1
      speed = min(fabs(speed), 8) * (1 if speed > 0 else -1)
      target_index = max(0, min(self.picsNode.getNumChildren()-1, target_index))
      target = -target_index * App.pic_stride
      self.interpolate("inertia", self.picsNode, 'x', target, speed)

if __name__ == '__main__':
  app = App()
  app.run()
