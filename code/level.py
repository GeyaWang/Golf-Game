import pygame
from player import Player, PlayerSpriteGroup
from tile import Tile, TileType, TileMaterial
from settings import TILE_WIDTH
from hitbox import HitboxSpriteGroup


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
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 1]
]


class Level:
    def __init__(self, screen):
        # sprite setup
        self.screen = screen
        self.collision_sprites = pygame.sprite.Group()
        self.sprite_group = HitboxSpriteGroup()
        self.player_group = PlayerSpriteGroup()

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
                    self.collision_sprites.add(tile)
                    self.sprite_group.add(tile)

        # spawn player
        player = Player((400, 150), self.collision_sprites)
        self.player_group.add(player)

    def draw_sprites(self):
        self.sprite_group.draw(self.screen)
        self.player_group.draw(self.screen)
