import pygame
from shapely.geometry import Point, LineString
from dataclasses import dataclass


class CircleHitbox:
    def __init__(self, r, pos: tuple | pygame.Vector2):
        self.screen = pygame.display.get_surface()
        self._radius = r
        self.pos = pos
        self._rect = pygame.Rect(self.pos[0], self.pos[1], self._radius, self._radius)
        self.hitbox = Point(self.pos).buffer(self._radius).boundary

    def update_pos(self):
        self._rect.x, self._rect.y = self.pos[0], self.pos[1]
        self.hitbox = Point(self.pos).buffer(self._radius).boundary

    def draw(self, colour, offset: pygame.Vector2):
        pygame.draw.circle(self.screen, colour, self._rect.topleft + offset, self._radius, 1)


class LineHitbox:
    def __init__(self, pos_list):
        self._screen = pygame.display.get_surface()
        self.pos_list = pos_list
        self.hitbox = LineString(pos_list)

    def draw(self, colour, offset: pygame.Vector2):
        prev_pos = None
        for pos in self.pos_list:
            if prev_pos is not None:
                pygame.draw.line(self._screen, colour, offset + prev_pos, offset + pos, 1)
            prev_pos = pos


@dataclass
class Hitbox:
    line: LineHitbox = None
    circles: list = None

    def draw(self, colour, offset: pygame.Vector2):
        if self.circles is not None:
            [x.draw(colour, offset) for x in self.circles]
        if self.line is not None:
            self.line.draw(colour, offset)
