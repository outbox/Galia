import sys
sys.path.append("./build/pynui")
from os import listdir
from pprint import pprint
from math import *
from time import clock

from pynui import *
from app.hands import *
from app.cursor import *
from app.thumbs import *
from app.helper import *

from panda3d.core import *
from direct.interval.MetaInterval import Sequence
from direct.showbase.ShowBase import ShowBase
from direct.task import Task

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
    self.thumbs = Thumbs()
    
    maker = CardMaker("")
    frameRatio = self.camLens.getAspectRatio()
    left = 0
    files = [self.image_path + f for f in listdir(self.image_path)][0:6]
    before = clock()
    print "Loading", len(files), "files..."
    for file in files:
      try:
         texture = loader.loadTexture(file)
      except:
        continue
      texture.setMinfilter(Texture.FTLinearMipmapLinear)
      texture.setWrapU(Texture.WMBorderColor)
      texture.setWrapV(Texture.WMBorderColor)
      texture.setBorderColor(VBase4(0,0,0,0))
      
      textureRatio = texture.getOrigFileXSize() * 1.0 / texture.getOrigFileYSize()
      
      pic = create_card(-1, 1, -1/frameRatio, 1/frameRatio, textureRatio)
      pic.reparentTo(self.picsNode)
      pic.setTexture(texture)
      pic.setPos(left, 0, 0)
      
      self.thumbs.add(texture)

      left += self.pic_stride
      
    print "Loaded in", str(clock() - before) + "s"

    self.cursor = Cursor(self)
    self.cursor_hand = None
    self.hand_tracker = HandTracker()
    self.accept('new-hand', self.new_hand)
    self.accept('lost-hand', self.lost_hand)
    self.accept('hand-grab-start', self.hand_grab_start)
    self.accept('hand-grab-end', self.hand_grab_end)
    self.accept('hand-move', self.hand_move)
    
    self.setupMirror()

    base.cTrav = CollisionTraverser('CollisionTraverser')

    pickerNode = CollisionNode('cursor')
    pickerNode.setFromCollideMask(Thumbs.CollisionMask)
    self.cursor_ray = CollisionRay(self.cam.getPos(), Vec3.unitZ())
    pickerNode.addSolid(self.cursor_ray)
    pickerNP = render.attachNewNode(pickerNode)
    self.collision_handler = CollisionHandlerEvent()
    self.collision_handler.addInPattern('%fn-into-%in')
    self.collision_handler.addAgainPattern('%fn-again-%in')
    self.collision_handler.addOutPattern('%fn-out-%in')
    base.cTrav.addCollider(pickerNP, self.collision_handler)

    self.taskMgr.add(self.update, 'UpdateTask')

    self.accept('goto-item', self.goto_item)

  def top(self, y = 0):
    return (y - self.cam.getPos().y) * tan(self.vfov()/2)

  def vfov(self):
    return radians(self.camLens.getVfov())
    
  def update(self, task):
    self.nui.update()
    self.hand_tracker.update(self.nui.users)
    return Task.cont

  def new_hand(self, hand):
    if self.cursor_hand: return
    self.cursor_hand = hand
    self.taskMgr.remove('zoom')
    offset = 0.3
    cubic_interpolate_pos('zoom', self.picsNode, 'y', offset)
    self.cursor.node.show()
    self.thumbs.fade(1)

  def lost_hand(self, hand):
    if hand != self.cursor_hand: return
    if len(self.hand_tracker.hands) > 0:
      self.cursor_hand = self.hand_tracker.hands.values()[0]
      if self.cursor_hand.grab: self.hand_grab_start(self.cursor_hand)
      return
    self.cursor_hand = None
    self.taskMgr.remove("zoom")
    cubic_interpolate_pos("zoom", self.picsNode, 'y', 0)
    cubic_interpolate_pos("zoom", self.picsNode, 'z', 0)
    self.cursor.node.hide()
    self.thumbs.fade(0)

  def hand_move(self, hand):
    if hand != self.cursor_hand: return
    if hand.grab:
      delta = hand.positions[-1].x - hand.positions[-2].x if len(hand.positions) > 1 else 0
      v = self.picsNode.getPos()
      self.picsNode.setPos(v.x + delta, v.y, v.z)
    
    self.cursor.set_side(hand.user_side[1])
    pos = hand.positions[-1]
    z = min(0, max(-0.2, -pos.z*2))
    y_scale = self.top(self.cursor.node.getPos().y)
    self.cursor.node.setPos(pos.x, z, min(1, pos.y) * y_scale)
    self.cursor_ray.setDirection(self.cursor.node.getPos() - self.cam.getPos())

  def hand_grab_start(self, hand):
    if hand != self.cursor_hand: return
    self.taskMgr.remove("inertia")
    self.cursor.set_drag(True)

  def hand_grab_end(self, hand):
    if hand != self.cursor_hand: return
    
    def index_for_position(pos):
      return floor(-pos / self.pic_stride + 0.5)

    self.cursor.set_drag(False)
    start = self.picsNode.getPos().x
    speed = hand.speeds[-1].x
    target_index = index_for_position(start)
    delta = hand.positions[-1].x - hand.positions[0].x
    if fabs(speed) > 2 and target_index == index_for_position(start - delta):
      target_index += 1 if speed < 0 else -1
    speed = min(fabs(speed), 8) * (1 if speed > 0 else -1)
    target_index = max(0, min(self.picsNode.getNumChildren()-1, target_index))
    target = -target_index * self.pic_stride
    cubic_interpolate_pos("inertia", self.picsNode, 'x', target, speed)

  def goto_item(self, index):
    target = -index * self.pic_stride
    cubic_interpolate_pos("inertia", self.picsNode, 'x', target)

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

    card.setShader(load_shader('reflection'))
    card.setTexture(buffer.getTexture())

    root.reparentTo(render)
    root.setMat(Mat4.rotateMat(-90, VBase3.unitX()) * Mat4.translateMat(0, 0, z))

if __name__ == '__main__':
  loadPrcFile("local-config.prc")
  app = App()
  app.run()
