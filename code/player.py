import pygame
import shapely
from tile import Tile
from settings import GRAVITY, FPS, PIXELS_PER_METER, PLAYER_RADIUS, HITBOX_TOLERANCE, TILE_WIDTH, DRAG_CONSTANT, PLAYER_MASS, SHOOT_STRENGTH_COEFFICIENT, DRAW_HITBOXES
from hitbox import CircleHitbox
from shapely.geometry import LineString
from math import dist as get_dist, floor, sqrt
from collections import namedtuple


class PlayerSpriteGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

    def shoot(self, pos):
        for sprite in self.sprites():
            sprite.shoot(pos)

    def draw(self, surface, bgsurf=None, special_flags=0):
        if DRAW_HITBOXES:
            for sprite in self.sprites():
                sprite.hitbox.draw()
        else:
            super().draw(surface)


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
        self.center = pygame.Vector2(self.rect.center)
        self.prev_pos_center = pygame.Vector2()
        self.hitbox = CircleHitbox(PLAYER_RADIUS, self.center)

    def shoot(self, pos):
        delta = pygame.Vector2(pos) - self.center
        self.velocity = delta.normalize() * sqrt(delta.magnitude()) * SHOOT_STRENGTH_COEFFICIENT

    def _rotate_sprite(self, angle):
        """Replace self.image with rotated sprite at a certain angle"""

        new_image = pygame.transform.rotate(self.sprite, angle)
        new_rect = new_image.get_rect()
        self.image = pygame.surface.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA, 32).convert_alpha()
        self.image.blit(new_image, ((self.rect.width - new_rect.width) / 2, (self.rect.height - new_rect.height) / 2))

    @staticmethod
    def _get_collisions(sprites: list[Tile], hitbox) -> list[Tile]:
        """Iterate through sprites to find instances of collisions"""

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
        """Set angular velocity, ignore if the change in position is negligible"""

        if get_dist(self.prev_pos_center, self.center) < HITBOX_TOLERANCE:
            self.angular_vel = 0
        else:
            self.angular_vel = self.velocity.dot(i_par) / (PLAYER_RADIUS / PIXELS_PER_METER)

    def _bounce(self, i_norm: pygame.Vector2, tile: Tile):
        """Bounce logic"""

        i_par = pygame.Vector2(i_norm.y, -i_norm.x)
        vel_norm = self.velocity.dot(i_norm) * -1 * tile.material.coef_restitution
        vel_par = self.velocity.dot(i_par) * tile.material.friction

        # ignore velocity component to the normal if negligible
        if abs(vel_norm) < 0.2:
            vel_norm = 0

        self.velocity.update(
            vel_norm * i_norm.x + vel_par * i_par.x,
            vel_norm * i_norm.y + vel_par * i_par.y
        )

        self._set_angular_vel(i_par)

    @staticmethod
    def _get_i_norm(hitbox, coord) -> pygame.Vector2 | None:
        """Find impulse vector in the direction of the normal"""

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
        ray_cast = LineString([(self.prev_pos_center.x - tolerance.x, self.prev_pos_center.y - tolerance.y), self.center])

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
                    distance = get_dist(coord, self.prev_pos_center)
                    i_norm = self._get_i_norm(hitbox, coord)
                    dot_prod = i_norm.dot(self.velocity)

                    # ignore if the normal vector does not oppose velocity
                    if i_norm.dot(self.velocity) > 0:
                        continue

                    if distance < min_dist or (distance == min_dist and dot_prod < min_dot_prod):
                        min_dist = distance
                        min_i_norm = self._get_i_norm(hitbox, coord)
                        min_dot_prod = min_i_norm.dot(self.velocity)
                        min_coord = coord
                        min_tile = tile

        return min_coord, min_i_norm, min_tile

    def _get_nearby_sprites(self) -> list[Tile]:
        """Get sprites in a 3 x 3 square"""

        sprite_list = []
        current_tile_x = TILE_WIDTH * floor(self.center.x / TILE_WIDTH)
        current_tile_y = TILE_WIDTH * floor(self.center.y / TILE_WIDTH)

        for sprite in self.collision_sprites:
            if max(abs(current_tile_x - sprite.pos[0]), abs(current_tile_y - sprite.pos[1])) <= TILE_WIDTH:
                sprite_list.append(sprite)

        return sprite_list

    def _apply_drag(self):
        """Apply drag opposing motion"""

        drag_magnitude = DRAG_CONSTANT * self.velocity.magnitude() ** 2
        drag_acceleration = drag_magnitude / PLAYER_MASS * -self.velocity
        self.velocity += drag_acceleration / FPS

    def _update_pos(self, *, coord=None, pos_change: pygame.Vector2 = None):
        """Update position using coord or change in position"""

        if coord is not None:

            # only coord or pos_change should be used
            if pos_change is not None:
                raise TypeError

            self.center.update(coord)
        elif pos_change is not None:
            self.center += pos_change

        self.rect.center = self.center
        self.hitbox.update_pos()

    def update(self):
        self.prev_pos_center.update(self.center)

        # rotate
        self.rotation += self.angular_vel
        self._rotate_sprite(self.rotation)

        # update position
        self._update_pos(pos_change=self.velocity * PIXELS_PER_METER / FPS)

        # prune sprites that are not close in proximity
        sprite_list = self._get_nearby_sprites()

        # check for collisions
        collided_sprites = self._get_collisions(sprite_list, self.hitbox)

        # accelerate due to gravity
        self.velocity.y += GRAVITY / FPS

        # collision logic
        if self.velocity.magnitude() != 0:
            coord, i_norm, tile = self._get_intersections(collided_sprites)

            # ignore if no collisions of perfectly grazing surface
            if coord is not None and i_norm.dot(self.velocity) != 0:
                # go to position
                self._update_pos(coord=coord)
                self._bounce(i_norm, tile)

        # calculate and apply drag force
        self._apply_drag()
