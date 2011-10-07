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