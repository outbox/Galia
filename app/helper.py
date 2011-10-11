from panda3d.core import *

def load_shader(name):
  return Shader.load("resources/shaders/" + name+ ".cg", Shader.SLCg)

def create_card(left, right, bottom, top, uv_ratio=1, name=""):
  maker = CardMaker(name)
  maker.setFrame(left, right, bottom, top)
  ratio = (right - left) * 1.0 / (top - bottom)
  if ratio > uv_ratio:
    diff = (ratio - uv_ratio) / 2
    maker.setUvRange(
      Point2(-diff, 0),
      Point2(1 + diff , 1))
  else:
    diff = (1/ratio - 1/uv_ratio) / 2
    maker.setUvRange(
      Point2(0, -diff),
      Point2(1, 1 + diff))
  return NodePath(maker.generate())

