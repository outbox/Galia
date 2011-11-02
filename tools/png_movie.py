import os, sys, argparse, os.path as path
from math import *
from fnmatch import fnmatch
import Image

parser = argparse.ArgumentParser(description='Convert a sequence of PNG images to one big image.')
parser.add_argument('path', help='path to look for images')
parser.add_argument('pattern', default='*', nargs='?', help='filter pattern for image files')
parser.add_argument('--output', default='out.png', required=False, help='output file name')
args = parser.parse_args()

files = [f for f in os.listdir(args.path) if fnmatch(f, args.pattern)]

width, height = Image.open(path.join(args.path, files[0])).size

side = sqrt(len(files))
n = 1
while n < side: n *=2
side = n

target = Image.new('RGBA', (side*width, side*height))

index = 0
for file in files:
  x = (index % side) * width
  y = (index // side) * height
  index += 1
  image = Image.open(path.join(args.path, file))
  target.paste(image, (x,y))

target.save(args.output)
