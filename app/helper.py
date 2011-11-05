from panda3d.core import *
from direct.task import Task
from math import *

def lerp(a, b, t):
  temp = a * (1 - t)
  temp += b * t # use += to support Panda's Mat4
  return temp

def cubic_interpolator(p0, p1, v0):
  a = p1*(-2.0) + v0 + p0*2.0
  b = p1 - a - v0 - p0
  return lambda t: ((a * t + b) * t + v0) * t + p0

def linear_interpolator(a, b):
  return lambda t: lerp(a, b, t)

def load_shader(name):
  return Shader.load("resources/shaders/" + name+ ".cg", Shader.SLCg)

def create_card(left, right, bottom, top, uv_ratio=1, name="", top_margin=0):
  maker = CardMaker(name)
  maker.setFrame(left, right, bottom, top)
  ratio = (right - left) * 1.0 / (top - bottom - top_margin)
  if ratio > uv_ratio:
    diff = (ratio - uv_ratio)*(1-top_margin) / 2
    maker.setUvRange(
      Point2(-diff, 0),
      Point2(1 + diff , 1 + top_margin))
  else:
    diff = (1/ratio - 1/uv_ratio) / 2
    maker.setUvRange(
      Point2(0, -diff),
      Point2(1, 1 + diff + top_margin))
  return NodePath(maker.generate())

def interpolate_task(task, interpolator, time, setter, on_done):
  a = min(1, task.time/time)
  setter(interpolator(a))
  if a < 1:
    return Task.cont
  else:
    if on_done: on_done()
    return Task.done

def interpolate(name, setter, interpolator, time, delay=0, on_done=None):
  task = PythonTask(interpolate_task, name)
  task.setDelay(delay)
  base.taskMgr.add(task, extraArgs=[task, interpolator, time, setter, on_done])
  return task

def cubic_interpolate(name, setter, start, end, speed=0, time=0.5, delay=0):
  return interpolate(name, setter, cubic_interpolator(start, end, speed), time, delay)

def cubic_interpolate_pos(name, node, target, speed=0, time=0.5):
  cubic_interpolate(name, node.setMat, node.getMat(), target, speed, time)

def vfov():
  return radians(base.camLens.getVfov())

def make_filter_buffer(srcbuffer, shader):
    blurBuffer=base.win.makeTextureBuffer('filter buffer', srcbuffer.getXSize(), srcbuffer.getYSize())
    blurBuffer.setClearColor(Vec4(0,0,0,0))
    blurCamera=base.makeCamera2d(blurBuffer)
    card = srcbuffer.getTextureCard()
    card.setShader(load_shader(shader))
    blurCamera.node().setScene(card)
    return blurBuffer
  
def make_fbo(auxrgba=0):
    winprops = WindowProperties()
    props = FrameBufferProperties()
    props.setRgbColor(1)
    props.setAlphaBits(1)
    props.setDepthBits(1)
    props.setAuxRgba(auxrgba)
    return base.graphicsEngine.makeOutput(
         base.pipe, "model buffer", -2,
         props, winprops,
         GraphicsPipe.BFSizeTrackHost | GraphicsPipe.BFCanBindEvery | 
         GraphicsPipe.BFRttCumulative | GraphicsPipe.BFRefuseWindow,
         base.win.getGsg(), base.win)

# Returns a rectangle of the desired aspect_ratio that fits inside a container
def fit(aspect_ratio, container_width, container_height):
  height = container_height
  width = height * aspect_ratio
  if width > container_width:
    width = container_width
    height = width / aspect_ratio
  return (width, height)