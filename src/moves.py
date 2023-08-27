import pytweening

from constants import FPS


class SpriteMoves:
    def __init__(self):
        self.moves = []

    def update(self):
        self.moves = [move.update() for move in self.moves if move.step < 1]

    def add_anchored_offset(self, target_object, target_x, target_y, time=1.0, easing=pytweening.easeInOutCubic):
        self.moves.append(AnchoredOffset(target_object, target_x, target_y, time, easing))

    def add_relative_move(self, target_object, target_x, target_y, time=1.0, easing=pytweening.easeInOutCubic):
        self.moves.append(RelativeMove(target_object, target_x, target_y, time, easing))

    def add_absolute_move(self, target_object, target_x, target_y, time=1.0, easing=pytweening.easeInOutCubic):
        self.moves.append(AbsoluteMove(target_object, target_x, target_y, time, easing))


class AbstractMove:
    def __init__(self, target_object, target_x, target_y, time, easing):
        self.target_object = target_object
        self.target_x = target_x
        self.target_y = target_y
        self.d_step = 1 / (FPS * time)
        self.step = 0
        self.easing = easing

    def update_step_and_rect(self):
        self.step += self.d_step
        self.target_object.rect.center = round(self.target_object.x), round(self.target_object.y)
        return self


class AnchoredOffset(AbstractMove):
    def __init__(self, target_object, target_x, target_y, time, easing):
        super().__init__(target_object, target_x, target_y, time, easing)

    def update(self):
        x, y = pytweening.getPointOnLine(self.target_x, self.target_y, 0, 0, self.easing(self.step))
        self.target_object.x += x
        self.target_object.y += y
        return super().update_step_and_rect()


class RelativeMove(AbstractMove):
    def __init__(self, target_object, target_x, target_y, time, easing):
        super().__init__(target_object, target_x, target_y, time, easing)

    def update(self):
        next_step = min(1, self.step + self.d_step)
        x1, y1 = pytweening.getPointOnLine(0, 0, self.target_x, self.target_y, self.easing(self.step))
        x2, y2 = pytweening.getPointOnLine(0, 0, self.target_x, self.target_y, self.easing(next_step))
        x = x2 - x1
        y = y2 - y1
        self.target_object.x += x
        self.target_object.y += y
        return super().update_step_and_rect()


class AbsoluteMove(AbstractMove):
    def __init__(self, target_object, target_x, target_y, time, easing):
        super().__init__(target_object, target_x, target_y, time, easing)
        self.initial_x = target_object.x
        self.initial_y = target_object.y

    def update(self):
        x, y = pytweening.getPointOnLine(self.initial_x, self.initial_y, self.target_x, self.target_y,
                                         self.easing(self.step))
        self.target_object.x = x
        self.target_object.y = y
        return super().update_step_and_rect()
