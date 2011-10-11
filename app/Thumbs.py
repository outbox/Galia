from panda3d.core import *
from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from app.helper import *

class Thumbs(DirectObject):
  CollisionMask = BitMask32(0x10)

  def __init__(self):
    self.start_task = PythonTask(self.start_interaction, 'ThumbsStartInteraction')
    self.start_task.setDelay(1)
    self.stop_task = PythonTask(self.stop_interaction, 'ThumbsStopInteraction')
    self.stop_task.setDelay(1)

    self.node = render.attachNewNode('Thumbs')
    self.node.setTransparency(TransparencyAttrib.MAlpha, 1)
    self.node.setSa(0)
    
    self.accept('cursor-into-thumb', self.cursor_into)
    self.accept('cursor-out-thumb', self.cursor_out)

    self.index = {}

    self.interacting = False
    self.hover_thumb = None

  def add(self, texture):
    stride = 2.05
    frameRatio = base.camLens.getAspectRatio()
    textureRatio = texture.getOrigFileXSize() * 1.0 / texture.getOrigFileYSize()
    thumb = create_card(-1, 1, -1/frameRatio, 1/frameRatio, textureRatio, 'thumb')
    self.index[thumb] = self.node.getNumChildren()
    thumb.setTexture(texture)
    thumb.setPos(self.node.getNumChildren() * stride, 0, 0);
    thumb.setCollideMask(Thumbs.CollisionMask)
    thumb.reparentTo(self.node)
    thumb.setTransparency(TransparencyAttrib.MAlpha, 1)
    thumb.setShader(load_shader('image'))

    scale = min(2/(self.node.getNumChildren() * stride), 0.1)
    self.node.setScale(scale)
    count = self.node.getNumChildren()
    self.node.setPos(-scale * count, 0, base.top() * (1 - scale))

  def fade_task(self, task, start, end, time):
    a = min(1, task.time/time)
    self.node.setSa(a*end + (1-a)*start)
    return Task.cont if a < 1 else Task.done

  def fade(self, to, time=0.5):
    base.taskMgr.remove('Fade')
    task = PythonTask(self.fade_task, 'Fade')
    base.taskMgr.add(task, extraArgs=[task, self.node.getSa(), to, time])
  
  def cursor_into(self, entry):
    base.taskMgr.remove(self.stop_task)
    self.hover_thumb = entry.getIntoNodePath()
    if not self.interacting:
      base.taskMgr.remove(self.start_task)
      base.taskMgr.add(self.start_task)
    else:
      self.goto(self.hover_thumb)

  def cursor_out(self, entry):
    self.hover_thumb = None
    base.taskMgr.remove(self.stop_task)
    base.taskMgr.add(self.stop_task)

  def start_interaction(self, task):
    self.interacting = True
    self.goto(self.hover_thumb)

  def stop_interaction(self, task):
    self.interacting = False

  def goto(self, thumb):
    if thumb:
      messenger.send('goto-item', [self.index[thumb]])