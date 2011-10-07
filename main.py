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
    size = 0.06
    maker = CardMaker("")
    maker.setFrame(-size/2, size/2, -size, 0)

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
    self.node.setTransparency(TransparencyAttrib.MAlpha, 1)
    self.node.setTwoSided(True)
    self.node.reparentTo(app.render)
    self.node.hide()

  def set_side(self, side):
    self.node.setScale(1 if side == Skeleton.right else -1, 1, 1)

  def set_drag(self, drag):
    self.node.setTexture(self.drag_texture if drag else self.texture)

CollisionMask = BitMask32(0x10)

class App(ShowBase):
  def __init__(self):
    ShowBase.__init__(self)

    self.image_path = "images/"
    self.pic_stride = 2.05

    base.disableMouse()

    self.win.setClearColor(VBase4(0, 0, 0, 0))

    self.nui = Nui()
    self.nui.smooth_factor = 0.8
    
    self.cam.setPos(0, -1, 0)
    self.camLens.setFov(90)
    self.camLens.setNear(0.01)
    self.camLens.setFar(2)

    self.picsNode = render.attachNewNode("Pics")
    self.thumbsNode = render.attachNewNode("Thumbs")
    self.thumbsNode

    maker = CardMaker("")
    frameRatio = self.camLens.getAspectRatio()
    print frameRatio
    left = 0
    files = [self.image_path + f for f in os.listdir(self.image_path)][0:6]
    before = clock()
    print "Loading", len(files), "files..."
    index = 0
    for file in files:
      try:
         texture = loader.loadTexture(file)
      except:
        continue
      texture.setMinfilter(Texture.FTLinearMipmapLinear)
      texture.setWrapU(Texture.WMBorderColor)
      texture.setWrapV(Texture.WMBorderColor)
      texture.setBorderColor(VBase4())
      
      textureRatio = texture.getOrigFileXSize() * 1.0 / texture.getOrigFileYSize()
      
      pic = createCard(-1, 1, -1/frameRatio, 1/frameRatio, textureRatio)
      pic.reparentTo(self.picsNode)
      pic.setTexture(texture)
      pic.setPos(left, 0, 0)
      
      thumb = createCard(-1, 1, -1/frameRatio, 1/frameRatio, textureRatio)
      thumb.reparentTo(self.thumbsNode)
      thumb.setTexture(texture)
      thumb.setTransparency(TransparencyAttrib.MAlpha, 1)
      thumb.setPos(left, 0, 0)
      thumb.setTag('index', str(index))
      thumb.setCollideMask(CollisionMask)

      left += self.pic_stride
      index += 1

    scale = min(2/left, 0.1)
    self.thumbsNode.setScale(scale)
    count = self.thumbsNode.getNumChildren()
    self.thumbsNode.setPos(-scale * count, 0, self.top() * (1 - scale))
      
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

    self.setupMirror()

    base.cTrav = CollisionTraverser('CollisionTraverser')

    pickerNode = CollisionNode('mouseRay')
    pickerNode.setFromCollideMask(CollisionMask)
    self.cursor_ray = CollisionRay(self.cam.getPos(), Vec3.unitZ())
    pickerNode.addSolid(self.cursor_ray)
    pickerNP = render.attachNewNode(pickerNode)
    self.collision_queue = CollisionHandlerQueue()
    base.cTrav.addCollider(pickerNP, self.collision_queue)

    self.taskMgr.add(self.update, "UpdateTask")

  def top(self, y = 0):
    return (y - self.cam.getPos().y) * tan(self.vfov()/2)

  def vfov(self):
    return radians(self.camLens.getVfov())
    
  def update(self, task):
    self.nui.update()
    self.touch_canvas.update(self.nui.users)

    base.cTrav.traverse(render)

    if self.collision_queue.getNumEntries() > 0:
      self.collision_queue.sortEntries()
      picked = self.collision_queue.getEntry(0).getIntoNodePath()
      print "collision", picked.getTag('index')

    return Task.cont

  def interpolate_task(self, task, interpolator, time, axis, node):
    a = min(1, task.time/time)
    v = node.getPos()
    v.__setattr__(axis, interpolator(a))
    node.setPos(v)
    return Task.cont if a < 1 else Task.done

  def fade_thumbs_task(self, task, start, end, time):
    a = min(1, task.time/time)
    for node in self.thumbsNode.getChildren():
      node.setSa(a*end + (1-a)*start)
    return Task.cont if a < 1 else Task.done

  def interpolate(self, name, node, axis, to, speed=0, time=0.5):
    v = node.getPos()
    interp = CubicInterpolator(v.__getattribute__(axis), to, speed)
    task = PythonTask(self.interpolate_task, name)
    self.taskMgr.add(task, extraArgs=[task, interp, time, axis, node])

  def fadeThumbs(self, to, time=0.5):
    self.taskMgr.remove("Fade")
    task = PythonTask(self.fade_thumbs_task, "Fade")
    self.taskMgr.add(task, extraArgs=[task, self.thumbsNode.getChildren()[0].getSa(), to, time])
    
  def cursor_appear(self):
    self.taskMgr.remove("zoom")
    offset = 0.3
    self.interpolate("zoom", self.picsNode, 'y', offset)
    self.hand.node.show()
    self.fadeThumbs(1)

  def cursor_disappear(self):
    self.taskMgr.remove("zoom")
    self.interpolate("zoom", self.picsNode, 'y', 0)
    self.interpolate("zoom", self.picsNode, 'z', 0)
    self.hand.node.hide()
    self.fadeThumbs(0)

  def cursor_move(self, pos, user, side):
    self.hand.set_side(side)
    z = min(0, max(-0.2, -pos.z*2))
    y_scale = self.top(self.hand.node.getPos().y)
    self.hand.node.setPos(pos.x, z, min(1, pos.y) * y_scale)
    self.cursor_ray.setDirection(self.hand.node.getPos() - self.cam.getPos())

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
    return floor(-pos / self.pic_stride + 0.5)
    
  def touch_up(self, touch):
    if touch == self.current_touch:
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
      target = -target_index * self.pic_stride
      self.interpolate("inertia", self.picsNode, 'x', target, speed)

  def setupMirror(self):
    name = 'mirror'
    width = height = 10
    z = -0.58
    root = render.attachNewNode(name)

    cm = CardMaker('mirror')
    cm.setFrame(-width / 2.0, width / 2.0, -height / 2.0, height / 2.0)
    
    card = root.attachNewNode(cm.generate())

    buffer = base.win.makeTextureBuffer(name, 1024, 1024)
    buffer.setClearColor(VBase4(0, 0, 0.01, 1))

    display = buffer.makeDisplayRegion()
    camera = Camera('mirror')
    cameraNP = render.attachNewNode(camera)
    display.setCamera(cameraNP)

    camera.setInitialState(RenderState.make(CullFaceAttrib.makeReverse())) 

    camera.setLens(base.camLens)
    symmetry = Mat4.translateMat(0,0,-z) * Mat4.scaleMat(1,1,-1) * Mat4.translateMat(0,0,z)
    cameraNP.setMat(base.cam.getMat() * symmetry)

    card.setShader(loadShader('reflection'))
    card.setTexture(buffer.getTexture())

    root.reparentTo(render)
    root.setMat(Mat4.rotateMat(-90, VBase3.unitX()) * Mat4.translateMat(0, 0, z))

def loadShader(name):
  return Shader.load("resources/shaders/" + name+ ".cg", Shader.SLCg)

def createCard(left, right, bottom, top, uvRatio=1):
  maker = CardMaker("")
  maker.setFrame(left, right, bottom, top)
  ratio = (right - left) * 1.0 / (top - bottom)
  if ratio > uvRatio:
    diff = (ratio - uvRatio) / 2
    maker.setUvRange(
      Point2(-diff, 0),
      Point2(1 + diff , 1))
  else:
    diff = (1/ratio - 1/uvRatio) / 2
    maker.setUvRange(
      Point2(0, -diff),
      Point2(1, 1 + diff))
  return NodePath(maker.generate())

if __name__ == '__main__':
  loadPrcFile("local-config.prc")
  app = App()
  app.run()
