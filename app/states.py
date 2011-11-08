from panda3d.core import *
from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from config import *

# Helper stuff

class State(DirectObject):
  def __init__(self):
    self.tasks = []

  def next_state(self, state):
    for task in self.tasks:
      base.taskMgr.remove(task)
    self.ignoreAll();
    print 'New state:', state

  def timer(self, time, function):
    self.tasks.append(base.taskMgr.doMethodLater(time, function, 'state timer', extraArgs=[]))

class UserState(State):
  def __init__(self, user):
    State.__init__(self)
    self.user = user
    self.accept('hand-move', self.hand_move)
    def lost_user(u):
      if u == user: 
        self.lost_user()
        self.next_state(Start())
    self.accept('lost-user', lost_user)

  def hand_move(self, hand):
    if self.user is None or hand.user == self.user:
      if hand.positions[-1].x * hand.side_sign > 0.35:
        self.hand_in(hand)
      elif hand.positions[-1].x * hand.side_sign < 0.3:
        self.hand_out(hand)

  def lost_user(self):
    pass

  def hand_in(self, hand):
    pass

  def hand_out(self, hand):
    pass


# State classes

class Start(UserState):
  def __init__(self):
    UserState.__init__(self, None)
    self.accept('space', self.thumbnails)
    self.timer(automatic_slide_interval, self.timeout)

  def timeout(self):
    if len(base.hand_tracker.hands) == 0:
      base.slide(1)
    self.timer(automatic_slide_interval, self.timeout)
  
  def hand_in(self, hand):
    self.next_state(Slide(hand, 1))

  def thumbnails(self):
    if not base.win.isFullscreen():
      self.next_state(Thumbnails(999))


class Slide(UserState):
  def __init__(self, hand, time):
    UserState.__init__(self, hand.user)
    self.hand = hand
    self.timer(time, self.timeout)
    base.slide(hand.side_sign)

  def hand_in(self, hand):
    if hand.side != self.hand.side and hand.user == self.hand.user:
      self.next_state(Thumbnails(self.hand.user))

  def timeout(self):
    self.next_state(Slide(self.hand, 0.5))
  
  def hand_out(self, hand):
    if hand.user_side == self.hand.user_side:
      self.next_state(Start())

class Thumbnails(UserState):
  def __init__(self, user, reflow = True):
    UserState.__init__(self, user)
    base.arrange_thumbnails(user, reflow)
    
    self.accept('cursor-into-pic', self.cursor_into_pic)
    self.accept('cursor-again-pic', self.cursor_into_pic)

    self.timer(4, self.timeout)

  def cursor_into_pic(self, entry):
    pic = entry.getIntoNodePath()
    if base.taskMgr.hasTaskNamed(str(pic.getKey())): return
    self.next_state(ThumbnailHover(self.user, pic))
  
  def lost_user(self):
    base.cursor.hide()
    base.arrange_normal()

  def timeout(self):
    base.arrange_thumbnails(self.user, reflow=True)
    self.timer(4, self.timeout)

class ThumbnailHover(UserState):
  def __init__(self, user, pic):
    UserState.__init__(self, user)
    self.pic = pic
    base.highlight_pic(pic)
    base.cursor.play_timer()
    self.accept('cursor-out-pic', self.cursor_out)
    self.accept('cursor-timer-end', self.timer_end)

  def cursor_out(self, entry):
    if self.pic != entry.getIntoNodePath(): return
    base.cursor.cancel_timer()
    self.next_state(Thumbnails(self.user, reflow=False))

  def timer_end(self):
    base.select_pic(self.pic)
    base.arrange_normal()
    self.next_state(Start())

  def lost_user(self):
    base.arrange_normal()
    base.cursor.hide()
