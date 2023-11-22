import pygame
from settings import DRAW_HITBOXES
from shapely.geometry import Point, LineString
from dataclasses import dataclass


class HitboxSpriteGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

    def draw(self, surface, bgsurf=None, special_flags=0):
        super().draw(surface)
        if DRAW_HITBOXES:
            for sprite in self.sprites():
                sprite.hitbox.draw('red')
                sprite.c_hitbox.draw('green')


class CircleHitbox:
    def __init__(self, r, pos: tuple | pygame.Vector2):
        self.screen = pygame.display.get_surface()
        self.radius = r
        self.pos = pos
        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.radius, self.radius)
        self.hitbox = Point(self.pos).buffer(self.radius).boundary

    def update_pos(self):
        self.rect.x, self.rect.y = self.pos[0], self.pos[1]
        self.hitbox = Point(self.pos).buffer(self.radius).boundary

    def draw(self, colour):
        pygame.draw.circle(self.screen, colour, self.rect.topleft, self.radius, 1)


class LineHitbox:
    def __init__(self, pos_list):
        self.screen = pygame.display.get_surface()
        self.pos_list = pos_list
        self.hitbox = LineString(pos_list)

    def draw(self, colour):
        prev_pos = None
        for pos in self.pos_list:
            if prev_pos is not None:
                pygame.draw.line(self.screen, colour, prev_pos, pos, 1)
            prev_pos = pos


@dataclass
class Hitbox:
    line: LineHitbox = None
    circles: list = None

    def draw(self, colour):
        if self.circles is not None:
            [x.draw(colour) for x in self.circles]
        if self.line is not None:
            self.line.draw(colour)
