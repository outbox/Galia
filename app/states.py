from panda3d.core import *
from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from config import *
from arrow import Arrow

# Helper stuff

hand_trigger = 0.35

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
      if hand.positions[-1].x * hand.side_sign >= hand_trigger:
        self.hand_in(hand)
      elif hand.positions[-1].x * hand.side_sign < hand_trigger:
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
    self.arrows = {}

  def timeout(self):
    if len(base.hand_tracker.hands) == 0:
      base.slide(1)
    self.timer(automatic_slide_interval, self.timeout)

  def next_state(self, state):
    for a in self.arrows.values(): a.destroy()
    self.arrows.clear()
    UserState.next_state(self, state)
  
  def thumbnails(self):
    if not base.win.isFullscreen():
      self.next_state(Thumbnails(999))

  def hand_in(self, hand):
    self.next_state(Slide(hand, 1))

  def hand_move(self, hand):
    arrow = self.arrows.get(hand.user_side, None)
    start = 0.1
    pos = hand.positions[-1].x * hand.side_sign
    if pos > start:
      if not arrow:
        self.arrows[hand.user_side] = arrow = Arrow(hand.user, hand.side)
      arrow.set_time_at_hint((pos - start) / (hand_trigger - start))
      arrow.update(base.nui.users)
    elif arrow:
      arrow.destroy()
      del self.arrows[hand.user_side]
    UserState.hand_move(self, hand)

class Slide(UserState):
  def __init__(self, hand, time, arrow=None):
    UserState.__init__(self, hand.user)
    self.hand = hand
    self.timer(time, self.timeout)
    base.slide(hand.side_sign)

    self.arrow = arrow
    if not self.arrow:
      self.arrow = Arrow(hand.user, hand.side)
      self.arrow.play_trigger()
    self.arrow.update(base.nui.users)

  def hand_move(self, hand):
    if hand.side == self.hand.side and not self.arrow.is_playing:
      max = 0.55
      pos = hand.positions[-1].x * hand.side_sign
      self.arrow.set_time_at_speed((pos - hand_trigger) / (max - hand_trigger))
    self.arrow.update(base.nui.users)
    UserState.hand_move(self, hand)

  def hand_in(self, hand):
    if hand.side != self.hand.side:
      self.arrow.destroy()
      self.next_state(Thumbnails(self.hand.user))

  def hand_out(self, hand):
    if hand.side == self.hand.side:
      self.arrow.destroy()
      self.next_state(Start())

  def lost_user(self):
    self.arrow.destroy()

  def timeout(self):
    self.next_state(Slide(self.hand, 0.5, self.arrow))
  
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
