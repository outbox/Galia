from panda3d.core import Vec2
from app.helper import fit
from math import *
from pprint import pprint

def get_nodes_size(nodes):
  items = []
  for node in nodes:
    texture = node.getTexture()
    items.append((node, Vec2(texture.getXSize() * 1.0 / texture.getYSize(), 1)))
  return items

class Flow(object):
  def __init__(self, nodes, container_width, container_height, spacing, margin):    
    nodes_size = get_nodes_size(nodes)

    one_row_width = 0
    for (node, size) in nodes_size:
      one_row_width += size.x + spacing

    container_ratio = (container_width - margin * 2) / (container_height - margin * 2)
    rows = round(sqrt(one_row_width / container_ratio))

    row_list = []
    target_row_width = one_row_width / rows
    row = []
    row_size = Vec2()
    top = 0
    for (node, size) in nodes_size:
      if row_size.x == 0 or row_size.x + spacing + size.x / 2 < target_row_width:
        if row_size.x > 0: row_size.x += spacing
        row_size.x += size.x
        row_size.y = max(size.y, row_size.y)
        row.append((node, size))
      else:
        row_list.append((row, row_size))
        top -= row_size.y + spacing
        row = [(node, size)]
        row_size = Vec2(size)
    row_list.append((row, row_size))

    total_width = 0
    total_height = 0
    for (row, size) in row_list:
      total_width = max(size.x, total_width)
      if total_height > 0: total_height += spacing
      total_height += size.y
    (width, height) = fit(
      total_width / total_height,
      container_width - margin * 2,
      container_height - margin * 2)

    self.scale = min(width / total_width, height / total_height)
    top = height + (container_height - height) / 2

    self.layout_items = []
    for (row, row_size) in row_list:
      left = -row_size.x / 2 * self.scale
      for (node, size) in row:
        scale = size / 2 * self.scale
        self.layout_items.append((node, Vec2(left + scale.x, top - scale.y), scale))
        left += (size.x + spacing) * self.scale
      top -= (1 + spacing) * self.scale
