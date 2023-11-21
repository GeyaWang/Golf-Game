import pygame
import shapely
from tile import Tile
from settings import GRAVITY, FPS, PIXELS_PER_METER, PLAYER_RADIUS, HITBOX_TOLERANCE, TILE_WIDTH, DRAG_CONSTANT, PLAYER_MASS
from hitbox import CircleHitbox
from shapely.geometry import LineString
from math import dist, floor


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, collision_sprites):
        super().__init__()

        self.collision_sprites = collision_sprites

        self.display_surf = pygame.display.get_surface()
        self.sprite = pygame.image.load('C:/Users/User/Desktop/Python/GolfGame/graphics/player/ball.png')
        self.image = self.sprite.copy()
        self.rect = self.image.get_rect(midbottom=pos)

        self.velocity = pygame.Vector2()
        self.rotation = 0

        self.angular_vel = 0
        self.pos = pygame.Vector2(self.rect.topleft)
        self.pos_center = pygame.Vector2()
        self.prev_pos_center = pygame.Vector2()
        self.hitbox = CircleHitbox(PLAYER_RADIUS, self.pos_center)

    def _rotate_sprite(self, angle):
        new_image = pygame.transform.rotate(self.sprite, angle)
        new_rect = new_image.get_rect()
        self.image = pygame.surface.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA, 32).convert_alpha()
        self.image.blit(new_image, ((self.rect.width - new_rect.width) / 2, (self.rect.height - new_rect.height) / 2))

    @staticmethod
    def _get_collisions(sprites: list[Tile], hitbox) -> list[Tile]:
        collided_sprites = []

        for sprite in sprites:
            if shapely.intersects(hitbox.hitbox, sprite.hitbox.line.hitbox):
                collided_sprites.append(sprite)

            if sprite.hitbox.circles is not None:
                for circle in sprite.hitbox.circles:
                    if shapely.intersects(hitbox.hitbox, circle.hitbox):
                        collided_sprites.append(sprite)
        return collided_sprites

    def _set_angular_vel(self, i_par: pygame.Vector2):
        if dist(self.prev_pos_center, self.pos_center) < 0.07:
            self.angular_vel = 0
        else:
            self.angular_vel = self.velocity.dot(i_par) / (PLAYER_RADIUS / PIXELS_PER_METER)

    def _bounce(self, i_norm: pygame.Vector2, tile: Tile):
        i_par = pygame.Vector2(i_norm.y, -i_norm.x)
        vel_norm = self.velocity.dot(i_norm) * -1 * tile.material.coef_restitution
        vel_par = self.velocity.dot(i_par) * tile.material.friction

        self.velocity.update(
            vel_norm * i_norm.x + vel_par * i_par.x,
            vel_norm * i_norm.y + vel_par * i_par.y
        )
        self._set_angular_vel(i_par)

    @staticmethod
    def _get_i_norm(hitbox, coord) -> pygame.Vector2 | None:
        # find normal impulse vector
        if isinstance(hitbox, CircleHitbox):
            circle_center = hitbox.pos
            i_norm = pygame.Vector2(coord[0] - circle_center[0], coord[1] - circle_center[1]).normalize()

        else:  # LineHitbox
            pos1, pos2 = None, None
            prev_pos = None
            for pos in hitbox.pos_list:
                if prev_pos is not None:
                    # test if intersection is on the line
                    # avoid division by zero
                    if pos[0] == prev_pos[0]:
                        if coord[0] == pos[0]:
                            pos1, pos2 = prev_pos, pos
                    elif abs(coord[1] - (((pos[1] - prev_pos[1]) / (pos[0] - prev_pos[0])) * (coord[0] - pos[0]) + pos[1])) < HITBOX_TOLERANCE:
                        pos1, pos2 = prev_pos, pos
                prev_pos = pos

            i_norm = pygame.Vector2(pos2[1] - pos1[1], pos1[0] - pos2[0]).normalize()
        return i_norm

    def _get_intersections(self, collided_tiles) -> tuple[tuple[float, float], pygame.Vector2, Tile]:
        """Iterate through collided tiles and find the intersections of closest proximity and opposition to motion"""

        # ray-cast from prev position and find intersection
        tolerance = self.velocity.normalize() * HITBOX_TOLERANCE
        ray_cast = LineString([(self.prev_pos_center.x - tolerance.x, self.prev_pos_center.y - tolerance.y), self.pos_center])

        min_dist = float('inf')
        min_dot_prod = float('inf')

        min_coord = None
        min_i_norm = None
        min_tile = None

        for tile in collided_tiles:
            sprite_hitbox = tile.c_hitbox

            for hitbox in (*sprite_hitbox.circles, sprite_hitbox.line):
                intersection = ray_cast.intersection(hitbox.hitbox)
                coords = []

                if not intersection.is_empty:
                    # get coord based on type of intersection

                    if isinstance(intersection, shapely.Point):
                        coords.append([*intersection.coords][0])

                    elif isinstance(intersection, shapely.MultiPoint):
                        for coord in intersection.geoms:
                            coords.append((coord.x, coord.y))

                for coord in coords:
                    distance = dist(coord, self.prev_pos_center)

                    if distance < min_dist:
                        min_dist = distance
                        min_i_norm = self._get_i_norm(hitbox, coord)
                        min_dot_prod = min_i_norm.dot(self.velocity)
                        min_coord = coord
                        min_tile = tile

                    elif distance == min_dist:
                        i_norm = self._get_i_norm(hitbox, coord)
                        dot_prod = min_i_norm.dot(self.velocity)

                        if dot_prod < min_dot_prod:
                            min_dot_prod = dot_prod
                            min_i_norm = i_norm
                            min_coord = coord
                            min_tile = tile

        return min_coord, min_i_norm, min_tile

    def update(self):
        self.prev_pos_center.update(self.pos_center)

        # rotate
        self.rotation += self.angular_vel
        self._rotate_sprite(self.rotation)

        # update position
        self.pos += self.velocity * PIXELS_PER_METER / FPS
        self.pos_center.update(self.pos.x + self.rect.width / 2, self.pos.y + self.rect.height / 2)
        self.rect.x, self.rect.y = self.pos.x, self.pos.y
        self.hitbox.update_pos()

        # prune sprites that are not close in proximity
        sprite_list = []
        current_tile_x = TILE_WIDTH * floor(self.pos.x / TILE_WIDTH)
        current_tile_y = TILE_WIDTH * floor(self.pos.y / TILE_WIDTH)
        for sprite in self.collision_sprites:
            if max(abs(current_tile_x - sprite.pos[0]), abs(current_tile_y - sprite.pos[1])) <= TILE_WIDTH:
                sprite_list.append(sprite)

        # check for collisions
        collided_sprites = self._get_collisions(sprite_list, self.hitbox)

        if not collided_sprites:
            # accelerate due to gravity
            self.velocity.y += GRAVITY / FPS

        if self.velocity.magnitude() != 0:
            coord, i_norm, tile = self._get_intersections(collided_sprites)

            # ignore if no collisions of perfectly grazing surface
            if coord is not None and i_norm.dot(self.velocity) != 0:
                # go to position
                self.pos_center.update(coord)
                self.pos.update(self.pos_center.x - self.rect.width / 2, self.pos_center.y - self.rect.height / 2),
                self.rect.x, self.rect.y = self.pos.x, self.pos.y

                self._bounce(i_norm, tile)
                self.hitbox.update_pos()

        # calculate and apply drag force
        drag_magnitude = DRAG_CONSTANT * (self.velocity.magnitude() ** 2 / 2)
        drag_acceleration = drag_magnitude / PLAYER_MASS * -self.velocity
        self.velocity += drag_acceleration / FPS
