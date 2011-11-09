from panda3d.core import *
from helper import *
from pynui import *

def scale_time(time, scale):
  return scale[0] + time * (scale[1] - scale[0])

class Arrow(object):
  hint = (0, 0.24)
  trigger = (0.24, 0.49)
  speed = (0.49, 1)

  def __init__(self, user, side):
    self.user = user
    self.side = side

    maker = CardMaker('')
    width = 0.2
    height = width / 2 * base.camLens.getAspectRatio()
    maker.setFrame(0, width, -height/2, height/2)
    self.node = render2d.attachNewNode(maker.generate())
    self.node.setTexture(loader.loadTexture('resources/arrow.png'))
    self.node.setTransparency(TransparencyAttrib.MAlpha, 1)

    if side == Skeleton.left:
      self.node.setScale(-1, 1, 1)

    self.set_time(0)

  def update(self, users):
    if self.user not in users: return
    skel_side = self.side.__get__(users[self.user])
    if not skel_side.shoulder.valid:
      print 'Arrow update: invalid shoulder'
      self.node.hide()
      return

    pos = skel_side.shoulder.projection
    if not pos or pos.isNan(): 
      print 'Arrow update: invalid shoulder pos', pos
      self.node.hide()
      return

    sign = 1 if self.side == Skeleton.right else -1
    world_pos = Point3(pos.x - 0.5 + 0.15 * sign, -pos.y, 0)
    mat = Mat4(base.cam.getMat())
    mat.invertInPlace()
    cam_pos = mat.xformPoint(world_pos)
    pos = Point2()
    project = base.camLens.project(Point3(cam_pos), pos)

    if project: 
      self.node.setPos(pos.x, 0, pos.y)
      self.node.show()
    else:
      self.node.hide()

  def set_time(self, time):
    time = max(0, min(1, time))
    mat = animation_transform(4, 8, time)
    self.node.setTexTransform(TextureStage.getDefault(), TransformState.makeMat3(mat))

  def set_time_at_hint(self, time):
    base.taskMgr.remove(self.animation_key)
    self.set_time(scale_time(time, Arrow.hint))

  def set_time_at_speed(self, time):
    base.taskMgr.remove(self.animation_key)
    self.set_time(scale_time(time, Arrow.speed))

  def play_trigger(self):
    interpolate(self.animation_key, self.set_time, lambda t: scale_time(t, Arrow.trigger), 0.2)

  @property
  def is_playing(self):
    return base.taskMgr.hasTaskNamed(self.animation_key)

  @property
  def animation_key(self):
    return str(self.node.getKey())

  def set_alpha(self, alpha):
    self.node.setColor(1,1,1,alpha)

  def destroy(self):
    base.taskMgr.remove(self.animation_key)
    interpolate(self.animation_key, self.set_alpha, lambda t: 1-t, 0.2, on_done=self.node.removeNode)
