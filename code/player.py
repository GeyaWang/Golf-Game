import pygame
import shapely
from tile import Tile
from settings import GRAVITY, FPS, PIXELS_PER_METER, PLAYER_RADIUS, HITBOX_TOLERANCE, TILE_WIDTH, DRAG_CONSTANT, PLAYER_MASS, SHOOT_STRENGTH_COEFFICIENT, VELOCITY_TOLERANCE
from hitbox import CircleHitbox
from shapely.geometry import LineString, GeometryCollection, Polygon, Point
from math import dist as get_dist, floor, sqrt


class Player(pygame.sprite.Sprite):
    def __init__(self, collision_sprites, pos=(0, 0)):
        super().__init__()

        self._collision_sprites = collision_sprites

        self._screen = pygame.display.get_surface()
        self._sprite = pygame.image.load('../graphics/player/ball.png')
        self.image = self._sprite.copy()
        self.rect = self.image.get_rect(center=pos)
        self.camera_offset = pygame.Vector2()

        self._velocity = pygame.Vector2()
        self._rotation = 0
        self._angular_vel = 0

        self.is_on_ground = False
        self.center = pygame.Vector2(self.rect.center)
        self.prev_pos_center = pygame.Vector2()
        self.hitbox = CircleHitbox(PLAYER_RADIUS, self.center)

    def shoot(self, pos):
        delta = pygame.Vector2(pos) - (self.center + self.camera_offset)
        self._velocity = delta.normalize() * sqrt(delta.magnitude()) * SHOOT_STRENGTH_COEFFICIENT

    def _rotate_sprite(self, angle):
        """Replace self.image with rotated sprite at a certain angle"""

        new_image = pygame.transform.rotate(self._sprite, angle)
        new_rect = new_image.get_rect()
        self.image = pygame.surface.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA, 32).convert_alpha()
        self.image.blit(new_image, ((self.rect.width - new_rect.width) / 2, (self.rect.height - new_rect.height) / 2))

    def _get_collisions(self, sprites: list[Tile]) -> list[Tile]:
        """Iterate through sprites to find instances of collisions"""

        # get travel hitbox
        hitbox_list = [
            Point(self.center).buffer(PLAYER_RADIUS).boundary,
            Point(self.prev_pos_center).buffer(PLAYER_RADIUS).boundary
        ]

        if self.center != self.prev_pos_center:
            offset = pygame.Vector2(self.center.y - self.prev_pos_center.y, self.prev_pos_center.x - self.center.x).normalize() * PLAYER_RADIUS

            hitbox_list.append(
                Polygon(
                    (
                        self.center + offset,
                        self.prev_pos_center + offset,
                        self.prev_pos_center - offset,
                        self.center - offset,
                        self.center + offset
                    )
                ),
            )

        travel_hitbox = GeometryCollection(hitbox_list)

        collided_sprites = []

        for sprite in sprites:
            if shapely.intersects(travel_hitbox, sprite.hitbox.line.hitbox):
                collided_sprites.append(sprite)

            if sprite.hitbox.circles is not None:
                for circle in sprite.hitbox.circles:
                    if shapely.intersects(travel_hitbox, circle.hitbox):
                        collided_sprites.append(sprite)

        return collided_sprites

    def _set_angular_vel(self, i_par: pygame.Vector2):
        """Set angular velocity, ignore if the change in position is negligible"""

        if self.is_stationary() or self._is_negligible_vel():
            self._angular_vel = 0
        else:
            self._angular_vel = self._velocity.dot(i_par) / (PLAYER_RADIUS / PIXELS_PER_METER)

    def _bounce(self, i_norm: pygame.Vector2, tile: Tile):
        """Bounce logic"""

        i_par = pygame.Vector2(i_norm.y, -i_norm.x)
        vel_norm = self._velocity.dot(i_norm) * -1 * tile.material.coef_restitution
        friction = 1 - (1 - tile.material.friction) / FPS * 60
        vel_par = self._velocity.dot(i_par) * friction

        # ignore velocity component to the normal if negligible
        if abs(vel_norm) < 0.2:
            vel_norm = 0

        self._velocity.update(
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
        tolerance = self._velocity.normalize() * HITBOX_TOLERANCE
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
                    dot_prod = i_norm.dot(self._velocity)

                    # ignore if the normal vector does not oppose velocity
                    if i_norm.dot(self._velocity) > 0:
                        continue

                    if distance < min_dist or (distance == min_dist and dot_prod < min_dot_prod):
                        min_dist = distance
                        min_i_norm = self._get_i_norm(hitbox, coord)
                        min_dot_prod = min_i_norm.dot(self._velocity)
                        min_coord = coord
                        min_tile = tile

        return min_coord, min_i_norm, min_tile

    def _get_nearby_sprites(self) -> list[Tile]:
        """Get sprites in a 3 x 3 square"""

        sprite_list = []
        current_tile_x = TILE_WIDTH * floor(self.center.x / TILE_WIDTH)
        current_tile_y = TILE_WIDTH * floor(self.center.y / TILE_WIDTH)

        for sprite in self._collision_sprites:
            if max(abs(current_tile_x - sprite.pos[0]), abs(current_tile_y - sprite.pos[1])) <= TILE_WIDTH:
                sprite_list.append(sprite)

        return sprite_list

    def _apply_drag(self):
        """Apply drag opposing motion"""

        drag_magnitude = DRAG_CONSTANT * self._velocity.magnitude() ** 2
        drag_acceleration = drag_magnitude / PLAYER_MASS * -self._velocity
        self._velocity += drag_acceleration / FPS

    def is_stationary(self) -> bool:
        return get_dist(self.prev_pos_center, self.center) < HITBOX_TOLERANCE and self._is_negligible_vel()

    def update_pos(self, *, coord=None, pos_change: pygame.Vector2 = None):
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

    def check_is_on_ground(self, sprites) -> bool:
        ray_cast = LineString([(self.center.x, self.center.y + PLAYER_RADIUS + HITBOX_TOLERANCE), self.center])

        for sprite in sprites:
            hitbox = sprite.hitbox

            if ray_cast.intersects(hitbox.line.hitbox):
                return True

            if hitbox.circles is None:
                continue

            for circle in hitbox.circles:
                if ray_cast.intersects(circle.hitbox):
                    return True
        return False

    def _is_negligible_vel(self) -> bool:
        return self._velocity.magnitude() < VELOCITY_TOLERANCE

    def update(self):
        super().update()

        self.prev_pos_center.update(self.center)

        # update position
        self.update_pos(pos_change=self._velocity * PIXELS_PER_METER / FPS)

        # accelerate due to gravity
        self._velocity.y += GRAVITY / FPS

        # prune sprites that are not close in proximity
        near_sprite_list = self._get_nearby_sprites()

        # check for collisions
        collided_sprites = self._get_collisions(near_sprite_list)

        # rotate
        self._rotation += self._angular_vel / FPS * 60
        self._rotate_sprite(self._rotation)

        # collision logic
        coord, i_norm, tile = self._get_intersections(collided_sprites)

        # ignore if no collisions of perfectly grazing surface
        if coord is not None and i_norm.dot(self._velocity) != 0:
            # go to position
            self.update_pos(coord=coord)

            if self._is_negligible_vel() and self.is_on_ground:
                self._velocity.update(0, 0)
            else:
                self._bounce(i_norm, tile)

        # calculate and apply drag force
        self._apply_drag()

        # check if grounded
        self.is_on_ground = self.check_is_on_ground(near_sprite_list)
