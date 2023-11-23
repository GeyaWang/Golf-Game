import pygame
from sys import exit as sys_exit
from settings import WIDTH, HEIGHT, FPS
from level import Level


class Game:
    def __init__(self):
        # pygame setup
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), vsync=1)
        self._clock = pygame.time.Clock()
        pygame.display.set_caption('Golf Game')

        self._level = Level(self.screen)

    def _run(self):
        """Game Loop"""

        while True:
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys_exit()

                elif event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    self._level.player.shoot(pos)

            # update
            self._level.player.update()

            # draw
            self.screen.fill('black')
            self._level.draw_sprites()
            pygame.display.flip()

            self._clock.tick(FPS)

    def start(self):
        self._run()


if __name__ == '__main__':
    game = Game()
    game.start()
