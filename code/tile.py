import pygame
from settings import TILE_WIDTH, PLAYER_RADIUS
from hitbox import Hitbox, LineHitbox, CircleHitbox
from enum import Enum, auto
from dataclasses import dataclass


class TileType:
    BLOCK = ((0, 0), (1, 0), (1, 1), (0, 1), (0, 0))
    SLOPE0 = ((0, 1), (1, 0), (1, 1), (0, 1))
    SLOPE1 = ((0, 0), (1, 1), (0, 1), (0, 0))
    SLOPE2 = ((0, 0), (1, 0), (0, 1), (0, 0))
    SLOPE3 = ((0, 0), (1, 0), (1, 1), (0, 0))


@dataclass
class Material:
    coef_restitution: float
    friction: float


class TileMaterial(Enum):
    GENERIC = Material(0.3, 0.95)


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, tile_type: tuple[tuple[int, int], ...], material: TileMaterial):
        super().__init__()

        self.pos = pos
        self.center = (pos[0] + TILE_WIDTH / 2, pos[1] + TILE_WIDTH / 2)
        self.material = material.value

        self.image = pygame.Surface([TILE_WIDTH, TILE_WIDTH])
        points = [(x * TILE_WIDTH, y * TILE_WIDTH) for x, y in tile_type]
        pygame.draw.polygon(self.image, 'white', points)
        self.rect = self.image.get_rect(topleft=self.pos)

        rel_points = [(x + self.pos[0], y + self.pos[1]) for x, y in points]
        self.hitbox = Hitbox(LineHitbox(rel_points))

        pos1 = None
        c_hitbox_points = []
        for pos2 in rel_points:
            if pos1 is not None:
                offset = pygame.Vector2(pos2[1] - pos1[1], pos1[0] - pos2[0]).normalize() * PLAYER_RADIUS
                c_hitbox_points += [(pos1[0] + offset.x, pos1[1] + offset.y), (pos2[0] + offset.x, pos2[1] + offset.y)]
            pos1 = pos2
        c_hitbox_points.append(c_hitbox_points[0])
        self.c_hitbox = Hitbox(line=LineHitbox(c_hitbox_points), circles=[CircleHitbox(PLAYER_RADIUS, x) for x in set(rel_points)])
