import pygame
from player import Player
from tile import Tile, TileType, TileMaterial
from settings import TILE_WIDTH
from camera import CameraSpriteGroup


LEVEL = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 4, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 3, 0, 1, 1, 3, 3, 3, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]


class Level:
    def __init__(self, screen):
        # sprite setup
        self._screen = screen
        self._collision_sprites = pygame.sprite.Group()
        self.player = Player(self._collision_sprites)
        self._visible_sprites = CameraSpriteGroup(self.player)

        # spawn tiles
        for y, column in enumerate(LEVEL):
            for x, tile_type in enumerate(column):
                if tile_type != 0:
                    pos = (x * TILE_WIDTH, y * TILE_WIDTH)
                    if tile_type == 1:
                        tile = Tile(pos, TileType.BLOCK, TileMaterial.GENERIC)
                    elif tile_type == 2:
                        tile = Tile(pos, TileType.SLOPE0, TileMaterial.GENERIC)
                    elif tile_type == 3:
                        tile = Tile(pos, TileType.SLOPE1, TileMaterial.GENERIC)
                    elif tile_type == 4:
                        tile = Tile(pos, TileType.SLOPE2, TileMaterial.GENERIC)
                    self._collision_sprites.add(tile)
                    self._visible_sprites.add(tile)

        # spawn player
        self.player.update_pos(coord=(150.8, 100))
        self._visible_sprites.add(self.player)

    def draw_sprites(self):
        self._visible_sprites.update()
        self._visible_sprites.draw(self._screen)
