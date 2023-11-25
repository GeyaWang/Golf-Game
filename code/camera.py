import pygame
from settings import DRAW_HITBOXES, CAMERA_SPEED
from player import Player
from tile import Tile


class CameraSpriteGroup(pygame.sprite.Group):
    def __init__(self, player):
        super().__init__()

        self._screen = pygame.display.get_surface()
        self._screen_center = self._screen.get_rect().center
        self._player = player
        self._target_offset = pygame.Vector2()
        self._offset = pygame.Vector2()

    def draw(self, surface, bgsurf=None, special_flags=0):
        if DRAW_HITBOXES:
            for sprite in self.sprites():
                if isinstance(sprite, Player):
                    sprite.hitbox.draw('blue', self._offset)
                elif isinstance(sprite, Tile):
                    sprite.hitbox.draw('red', self._offset)
                    sprite.c_hitbox.draw('lime', self._offset)
        else:
            for sprite in self.sprites():
                self._screen.blit(sprite.image, self._offset + sprite.rect.topleft)

    def update(self):
        if self._player.is_on_ground and self._player.is_stationary():
            self._target_offset = self._screen_center - self._player.center

        self._offset += (self._target_offset - self._offset) * CAMERA_SPEED
        self._player.camera_offset.update(self._offset)
