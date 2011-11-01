from panda3d.core import Vec2, Vec3
from app.helper import fit
from math import *
from pprint import pprint

class Flow(object):
  def __init__(self, items, container_width, container_height, spacing, margin):    
    one_row_width, average_height = 0, 0
    for (node, pos, scale) in items:
      one_row_width += scale.x * 2 + spacing
      average_height += scale.z * 2
    average_height /= len(items)
    one_row_width -= spacing

    wall_aspect = (container_width - margin * 2) / (container_height - margin * 2)
    rows = round(sqrt(one_row_width / (average_height * wall_aspect)))

    row_list = []
    target_row_width = one_row_width / rows
    row = []
    row_size = Vec2()
    top = 0
    for (node, pos, scale) in items:
      if row_size.x == 0 or row_size.x + spacing + scale.x < target_row_width:
        if row_size.x > 0: row_size.x += spacing
        row_size.x += scale.x * 2
        row_size.y = max(scale.z * 2, row_size.y)
        row.append((node, Vec3(row_size.x - scale.x, pos.y, top - scale.z), scale))
      else:
        row_list.append((row, row_size))
        top -= row_size.y + spacing
        row = [(node, Vec3(scale.x, pos.y, top - scale.z), scale)]
        row_size = Vec2(scale.x, scale.z) * 2
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
      for (pic, pos, scale) in row:
        target_pos = Vec3(
          (pos.x - row_size.x / 2) * self.scale,
          pos.y, 
          top + (pos.z - row_size.y / 2 + scale.z) * self.scale)
        target_scale = Vec3(scale.x * self.scale, scale.y, scale.z * self.scale)
        self.layout_items.append((pic, target_pos, target_scale))
