import arcade
import random
import math
from enum import Enum
import sqlite3

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Pac-Man: Dual Mode"
CELL_SIZE = 20
GRID_WIDTH = 28
GRID_HEIGHT = 31
FPS = 60

BLACK = arcade.color.BLACK
WHITE = arcade.color.WHITE
YELLOW = arcade.color.YELLOW
RED = arcade.color.RED
PINK = (255, 184, 255)
CYAN = arcade.color.CYAN
ORANGE = arcade.color.ORANGE
BLUE = arcade.color.BLUE
GREEN = arcade.color.GREEN
DARK_BLUE = arcade.color.DARK_BLUE
LIME = arcade.color.LIME

class Direction(Enum):
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)

MAZE = [
    "1111111111111111111111111111",
    "1............##............1",
    "1.1111.11111.##.11111.1111.1",
    "1O1111.11111.##.11111.1111O1",
    "1.1111.11111.##.11111.1111.1",
    "1..........................1",
    "1.1111.##.11111111.##.1111.1",
    "1.1111.##.11111111.##.1111.1",
    "1......##....##....##......1",
    "111111.11111.##.11111.111111",
    "111111.11111.##.11111.111111",
    "111111.##..........##.111111",
    "111111.##.111##111.##.111111",
    "111111.##.11111111.##.111111",
    "..........11111111..........",
    "111111.##.11111111.##.111111",
    "111111.##.11111111.##.111111",
    "111111.##..........##.111111",
    "111111.##.11111111.##.111111",
    "111111.##.11111111.##.111111",
    "1............##............1",
    "1.1111.11111.##.11111.1111.1",
    "1.1111.11111.##.11111.1111.1",
    "1O..##................##..O1",
    "111.##.##.11111111.##.##.111",
    "111.##.##.11111111.##.##.111",
    "1......##....##....##......1",
    "1.1111111111.##.1111111111.1",
    "1.1111111111.##.1111111111.1",
    "1..........................1",
    "1111111111111111111111111111"
]

class PacMan:
    def __init__(self, x: int, y: int, color, controls: str = "arrows"):
        self.center_x = x * CELL_SIZE + CELL_SIZE // 2
        self.center_y = (GRID_HEIGHT - 1 - y) * CELL_SIZE + CELL_SIZE // 2

        self.color = color
        self.controls = controls
        self.radius = CELL_SIZE // 2 - 2
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.speed = 2.0
        self.mouth_angle = 0
        self.mouth_speed = 8
        self.mouth_open = True
        self.power_mode = False
        self.power_timer = 0
        self.power_duration = 8 * FPS
        self.score = 0
        self.alive = True
        self.respawning = False
        self.respawn_timer = 0

    def update(self):
        self.mouth_angle += self.mouth_speed
        if self.mouth_angle > 45:
            self.mouth_angle = 0
            self.mouth_open = not self.mouth_open

        if self.power_mode:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.power_mode = False

        if self.respawning:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawning = False
                self.alive = True

    def move(self):
        if not self.alive or self.respawning:
            return

        grid_x = int(self.center_x // CELL_SIZE)
        grid_y = GRID_HEIGHT - 1 - int(self.center_y // CELL_SIZE)

        at_center_x = abs(self.center_x - (grid_x * CELL_SIZE + CELL_SIZE // 2)) < self.speed
        at_center_y = abs(self.center_y - (grid_y * CELL_SIZE + CELL_SIZE // 2)) < self.speed

        if at_center_x and at_center_y:
            if self.next_direction != self.direction and self.can_move(self.next_direction):
                self.direction = self.next_direction

        if self.can_move(self.direction):
            dx, dy = self.direction.value
            self.center_x += dx * self.speed
            self.center_y += dy * self.speed
        else:
            self.center_x = grid_x * CELL_SIZE + CELL_SIZE // 2
            self.center_y = (GRID_HEIGHT - 1 - grid_y) * CELL_SIZE + CELL_SIZE // 2

        if self.center_x < -CELL_SIZE:
            self.center_x = SCREEN_WIDTH + CELL_SIZE
        elif self.center_x > SCREEN_WIDTH + CELL_SIZE:
            self.center_x = -CELL_SIZE

    def can_move(self, direction: Direction) -> bool:
        if direction == Direction.NONE:
            return False

        dx, dy = direction.value
        new_x = self.center_x + dx * self.speed
        new_y = self.center_y + dy * self.speed

        check_points = [
            (new_x, new_y),
            (new_x - self.radius + 1, new_y - self.radius + 1),
            (new_x + self.radius - 1, new_y - self.radius + 1),
            (new_x - self.radius + 1, new_y + self.radius - 1),
            (new_x + self.radius - 1, new_y + self.radius - 1),
        ]

        for point_x, point_y in check_points:
            grid_x = int(point_x // CELL_SIZE)
            grid_y = GRID_HEIGHT - 1 - int(point_y // CELL_SIZE)

            if grid_x < 0 or grid_x >= GRID_WIDTH or grid_y < 0 or grid_y >= GRID_HEIGHT:
                continue

            if MAZE[grid_y][grid_x] == '1':
                return False

        return True

    def set_direction(self, direction: Direction):
        if direction != Direction.NONE:
            self.next_direction = direction
            if self.can_move(direction):
                self.direction = direction

    def draw(self):
        if not self.alive:
            return

        color = BLUE if self.power_mode else self.color

        angle_offset = {
            Direction.RIGHT: 0,
            Direction.UP: 90,
            Direction.LEFT: 180,
            Direction.DOWN: 270
        }.get(self.direction, 0)

        if self.mouth_open:
            start_angle = angle_offset + self.mouth_angle
            end_angle = angle_offset + 360 - self.mouth_angle

            arcade.draw_circle_filled(self.center_x, self.center_y,
                                      self.radius, color)

            mouth_radius = self.radius * 1.3
            point1 = (self.center_x, self.center_y)
            point2 = (
                self.center_x + mouth_radius * math.cos(math.radians(start_angle)),
                self.center_y + mouth_radius * math.sin(math.radians(start_angle))
            )
            point3 = (
                self.center_x + mouth_radius * math.cos(math.radians(end_angle)),
                self.center_y + mouth_radius * math.sin(math.radians(end_angle))
            )

            arcade.draw_triangle_filled(
                point1[0], point1[1],
                point2[0], point2[1],
                point3[0], point3[1],
                BLACK
            )
        else:
            arcade.draw_circle_filled(self.center_x, self.center_y,
                                      self.radius, color)

            eye_offset = {
                Direction.RIGHT: (self.radius // 3, self.radius // 3),
                Direction.UP: (0, self.radius // 2),
                Direction.LEFT: (-self.radius // 3, self.radius // 3),
                Direction.DOWN: (0, -self.radius // 4)
            }.get(self.direction, (0, 0))

            arcade.draw_circle_filled(
                self.center_x + eye_offset[0],
                self.center_y + eye_offset[1],
                self.radius // 4, BLACK
            )

    def activate_power(self):
        self.power_mode = True
        self.power_timer = self.power_duration

    def die(self):
        self.alive = False
        self.respawning = True
        self.respawn_timer = 3 * FPS

    def respawn(self, x: int, y: int):
        self.center_x = x * CELL_SIZE + CELL_SIZE // 2
        self.center_y = (GRID_HEIGHT - 1 - y) * CELL_SIZE + CELL_SIZE // 2
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.power_mode = False
        self.power_timer = 0
        self.alive = True
        self.respawning = False


class Ghost:
    def __init__(self, color, name: str, start_pos):
        self.center_x = start_pos[0] * CELL_SIZE + CELL_SIZE // 2
        self.center_y = (GRID_HEIGHT - 1 - start_pos[1]) * CELL_SIZE + CELL_SIZE // 2

        self.color = color
        self.name = name
        self.radius = CELL_SIZE // 2 - 3
        self.direction = Direction.LEFT
        self.speed = 1.5
        self.base_speed = 1.5
        self.frightened = False
        self.frightened_timer = 0
        self.frightened_duration = 7 * FPS
        self.eyes_only = False
        self.scatter_mode = False
        self.scatter_timer = 0
        self.scatter_duration = 7 * FPS
        self.chase_duration = 20 * FPS

        self.start_pos = start_pos

    def update(self):
        if self.frightened:
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.frightened = False
                self.speed = self.base_speed

        if not self.frightened and not self.eyes_only:
            self.scatter_timer += 1
            if self.scatter_mode:
                if self.scatter_timer >= self.scatter_duration:
                    self.scatter_mode = False
                    self.scatter_timer = 0
            else:
                if self.scatter_timer >= self.chase_duration:
                    self.scatter_mode = True
                    self.scatter_timer = 0

    def move(self):
        if self.center_x < -CELL_SIZE:
            self.center_x = SCREEN_WIDTH + CELL_SIZE
        elif self.center_x > SCREEN_WIDTH + CELL_SIZE:
            self.center_x = -CELL_SIZE

        if self.can_move(self.direction):
            dx, dy = self.direction.value
            self.center_x += dx * self.speed
            self.center_y += dy * self.speed
        else:
            self.choose_random_direction()

    def can_move(self, direction: Direction) -> bool:
        dx, dy = direction.value
        new_x = self.center_x + dx * self.speed
        new_y = self.center_y + dy * self.speed

        check_points = [
            (new_x, new_y),
            (new_x - self.radius + 1, new_y - self.radius + 1),
            (new_x + self.radius - 1, new_y - self.radius + 1),
            (new_x - self.radius + 1, new_y + self.radius - 1),
            (new_x + self.radius - 1, new_y + self.radius - 1)
        ]

        for point_x, point_y in check_points:
            grid_x = int(point_x // CELL_SIZE)
            grid_y = GRID_HEIGHT - 1 - int(point_y // CELL_SIZE)

            if grid_x < 0 or grid_x >= GRID_WIDTH or grid_y < 0 or grid_y >= GRID_HEIGHT:
                continue

            if MAZE[grid_y][grid_x] == '1':
                return False

        return True

    def choose_random_direction(self):
        possible_directions = []
        for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            if self.can_move(direction):
                possible_directions.append(direction)

        if possible_directions:
            self.direction = random.choice(possible_directions)
        else:
            self.direction = Direction.NONE

    def get_opposite_direction(self, direction: Direction) -> Direction:
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }
        return opposites.get(direction, Direction.NONE)

    def choose_direction(self, pacmen, other_ghosts):
        if self.eyes_only:
            self.return_to_home()
            return

        possible_directions = []
        for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            if direction != self.get_opposite_direction(self.direction):
                if self.can_move(direction):
                    possible_directions.append(direction)

        if not possible_directions:
            possible_directions = [self.get_opposite_direction(self.direction)]

        if self.frightened:
            if possible_directions:
                self.direction = random.choice(possible_directions)
            return

        if self.scatter_mode and not self.frightened:
            target_x, target_y = self.get_scatter_target()
        else:
            if pacmen:
                alive_pacmen = [p for p in pacmen if p.alive]
                if alive_pacmen:
                    target_pacman = min(alive_pacmen,
                                        key=lambda p: ((self.center_x - p.center_x) ** 2 +
                                                       (self.center_y - p.center_y) ** 2) ** 0.5)
                    target_x, target_y = self.get_chase_target(target_pacman, other_ghosts)
                else:
                    self.return_to_home()
                    return
            else:
                target_x, target_y = self.get_scatter_target()

        if possible_directions:
            best_direction = possible_directions[0]
            best_distance = float('inf')

            for direction in possible_directions:
                dx, dy = direction.value
                new_x = self.center_x + dx * CELL_SIZE * 2
                new_y = self.center_y + dy * CELL_SIZE * 2
                distance = ((new_x - target_x) ** 2 + (new_y - target_y) ** 2) ** 0.5

                if distance < best_distance:
                    best_distance = distance
                    best_direction = direction

            self.direction = best_direction

    def get_scatter_target(self):
        corners = {
            "Blinky": (GRID_WIDTH - 2, 1),
            "Pinky": (2, 1),
            "Inky": (GRID_WIDTH - 2, GRID_HEIGHT - 2),
            "Clyde": (2, GRID_HEIGHT - 2)
        }

        corner_x, corner_y = corners.get(self.name, (GRID_WIDTH // 2, GRID_HEIGHT // 2))
        return (corner_x * CELL_SIZE + CELL_SIZE // 2,
                (GRID_HEIGHT - 1 - corner_y) * CELL_SIZE + CELL_SIZE // 2)

    def get_chase_target(self, pacman: PacMan, other_ghosts):
        if self.name == "Blinky":
            return pacman.center_x, pacman.center_y

        elif self.name == "Pinky":
            dx, dy = pacman.direction.value
            target_x = pacman.center_x + dx * CELL_SIZE * 4
            target_y = pacman.center_y + dy * CELL_SIZE * 4
            return target_x, target_y

        elif self.name == "Inky":
            blinky = next((g for g in other_ghosts if g.name == "Blinky"), None)
            if blinky:
                dx, dy = pacman.direction.value
                pivot_x = pacman.center_x + dx * CELL_SIZE * 2
                pivot_y = pacman.center_y + dy * CELL_SIZE * 2

                target_x = 2 * pivot_x - blinky.center_x
                target_y = 2 * pivot_y - blinky.center_y
                return target_x, target_y

        elif self.name == "Clyde":
            distance = ((self.center_x - pacman.center_x) ** 2 +
                        (self.center_y - pacman.center_y) ** 2) ** 0.5
            if distance > CELL_SIZE * 8:
                return pacman.center_x, pacman.center_y

        return self.get_scatter_target()

    def return_to_home(self):
        home_x, home_y = self.start_pos
        target_x = home_x * CELL_SIZE + CELL_SIZE // 2
        target_y = (GRID_HEIGHT - 1 - home_y) * CELL_SIZE + CELL_SIZE // 2

        if (abs(self.center_x - target_x) < 5 and
                abs(self.center_y - target_y) < 5):
            self.eyes_only = False
            self.frightened = False
            self.speed = self.base_speed
            return

        possible_directions = []
        for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            if direction != self.get_opposite_direction(self.direction):
                if self.can_move(direction):
                    possible_directions.append(direction)

        if not possible_directions:
            possible_directions = [self.get_opposite_direction(self.direction)]

        if possible_directions:
            best_direction = possible_directions[0]
            best_distance = float('inf')

            for direction in possible_directions:
                dx, dy = direction.value
                new_x = self.center_x + dx * CELL_SIZE * 2
                new_y = self.center_y + dy * CELL_SIZE * 2
                distance = ((new_x - target_x) ** 2 + (new_y - target_y) ** 2) ** 0.5

                if distance < best_distance:
                    best_distance = distance
                    best_direction = direction

            self.direction = best_direction
            self.speed = self.base_speed * 2

    def draw(self):
        if self.eyes_only:
            arcade.draw_circle_filled(self.center_x, self.center_y,
                                      self.radius, WHITE)

            pupil_offset = {
                Direction.LEFT: (-self.radius // 3, 0),
                Direction.RIGHT: (self.radius // 3, 0),
                Direction.UP: (0, self.radius // 3),
                Direction.DOWN: (0, -self.radius // 3)
            }.get(self.direction, (0, 0))

            arcade.draw_circle_filled(
                self.center_x + pupil_offset[0],
                self.center_y + pupil_offset[1],
                self.radius // 3, BLUE
            )
        else:
            body_color = BLUE if self.frightened else self.color
            arcade.draw_circle_filled(self.center_x, self.center_y,
                                      self.radius, body_color)

            points = []
            for i in range(7):
                angle = i * 51.4
                x = self.center_x + self.radius * 0.9 * math.cos(math.radians(angle))
                y = self.center_y + self.radius * 0.9 * math.sin(math.radians(angle)) - 7
                points.append((x, y))
            arcade.draw_polygon_filled(points, body_color)

            eye_radius = self.radius // 2.5
            left_eye_x = self.center_x - eye_radius
            right_eye_x = self.center_x + eye_radius
            eyes_y = self.center_y + eye_radius

            arcade.draw_circle_filled(left_eye_x, eyes_y, eye_radius, WHITE)
            arcade.draw_circle_filled(right_eye_x, eyes_y, eye_radius, WHITE)

            pupil_offset = {
                Direction.LEFT: (-eye_radius // 1.5, 0),
                Direction.RIGHT: (eye_radius // 1.5, 0),
                Direction.UP: (0, eye_radius // 1.5),
                Direction.DOWN: (0, -eye_radius // 1.5)
            }.get(self.direction, (0, 0))

            arcade.draw_circle_filled(left_eye_x + pupil_offset[0],
                                      eyes_y + pupil_offset[1],
                                      eye_radius // 2, BLUE)
            arcade.draw_circle_filled(right_eye_x + pupil_offset[0],
                                      eyes_y + pupil_offset[1],
                                      eye_radius // 2, BLUE)

    def activate_frightened(self):
        if not self.eyes_only:
            self.frightened = True
            self.frightened_timer = self.frightened_duration
            self.speed = self.base_speed * 0.7

    def die(self):
        self.eyes_only = True
        self.frightened = False

    def respawn(self):
        self.center_x = self.start_pos[0] * CELL_SIZE + CELL_SIZE // 2
        self.center_y = (GRID_HEIGHT - 1 - self.start_pos[1]) * CELL_SIZE + CELL_SIZE // 2
        self.direction = Direction.LEFT
        self.frightened = False
        self.eyes_only = False
        self.frightened_timer = 0
        self.speed = self.base_speed


class PacManGame(arcade.View):
    def __init__(self):
        super().__init__()

        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        self.pacman1 = None
        self.pacman2 = None
        self.pacmen = []

        self.ghosts = []

        self.dots = []
        self.energizers = []
        self.walls = []

        self.score_text = None
        self.lives_text = None

        self.game_started = False
        self.game_over = False
        self.game_won = False
        self.paused = False
        self.total_score = 0
        self.shared_lives = 5
        self.frame_count = 0

        self.player1_name = self.load_player_name(1)
        self.player2_name = self.load_player_name(2)

        arcade.set_background_color(BLACK)
        self.setup()

    def setup(self):
        self.game_over = False
        self.game_won = False
        self.paused = False
        self.total_score = 0
        self.shared_lives = 5
        self.frame_count = 0

        self.dots = []
        self.energizers = []
        self.walls = []
        self.ghosts = []
        self.pacmen = []

        for y, row in enumerate(MAZE):
            for x, cell in enumerate(row):
                if cell == '1':
                    self.walls.append((x, y))
                elif cell == '.':
                    self.dots.append((x, y))
                elif cell == 'O':
                    self.energizers.append((x, y))

        self.pacman1 = PacMan(13, 23, YELLOW, "arrows")
        self.pacman2 = PacMan(14, 23, LIME, "wasd")
        self.pacmen = [self.pacman1, self.pacman2]

        ghost_start_pos = (13, 11)
        ghost_data = [
            (RED, "Blinky"),
            (PINK, "Pinky"),
            (CYAN, "Inky"),
            (ORANGE, "Clyde")
        ]

        for color, name in ghost_data:
            ghost = Ghost(color, name, ghost_start_pos)
            self.ghosts.append(ghost)

        window = self.window
        self.score_text = arcade.Text("", 10, window.height - 30, arcade.color.WHITE, 24, bold=True)
        self.lives_text = arcade.Text("", window.width - 150, window.height - 30, arcade.color.WHITE, 24, bold=True)

    def load_player_name(self, player_id):
        self.cursor.execute(f"SELECT name FROM data_player{player_id} WHERE id = 0")
        result = self.cursor.fetchone()
        return result[0] if result else f"Игрок {player_id}"

    def on_show(self):
        arcade.set_background_color(BLACK)

    def on_draw(self):
        self.clear()

        window = self.window

        if not self.game_started and not self.game_over and not self.game_won:
            arcade.draw_text("Командный Pac-Man", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140,
                             arcade.color.WHITE, 32, bold=True, anchor_x="center")
            arcade.draw_text("Нажмите: Space - чтобы начать, Esc - чтобы выйти", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2, arcade.color.WHITE, 24, anchor_x="center")
            return

        for x, y in self.walls:
            screen_x = x * CELL_SIZE + CELL_SIZE // 2
            screen_y = (GRID_HEIGHT - 1 - y) * CELL_SIZE + CELL_SIZE // 2
            wall_rect = arcade.rect.XYWH(screen_x, screen_y, CELL_SIZE, CELL_SIZE)
            arcade.draw_rect_filled(wall_rect, DARK_BLUE)

        for x, y in self.dots:
            screen_x = x * CELL_SIZE + CELL_SIZE // 2
            screen_y = (GRID_HEIGHT - 1 - y) * CELL_SIZE + CELL_SIZE // 2
            arcade.draw_circle_filled(screen_x, screen_y, 3, WHITE)

        for x, y in self.energizers:
            screen_x = x * CELL_SIZE + CELL_SIZE // 2
            screen_y = (GRID_HEIGHT - 1 - y) * CELL_SIZE + CELL_SIZE // 2
            size = 6 + 2 * math.sin(self.frame_count * 0.1)
            arcade.draw_circle_filled(screen_x, screen_y, size, WHITE)

        for ghost in self.ghosts:
            ghost.draw()

        for pacman in self.pacmen:
            pacman.draw()

        self.score_text.text = f"Score: {self.total_score}"
        self.lives_text.text = f"Lives: {self.shared_lives}"
        self.score_text.draw()
        self.lives_text.draw()

        for i in range(min(self.shared_lives - 1, 5)):
            size = 8
            x = window.width - 120 + i * 25
            y = window.height - 60
            arcade.draw_circle_filled(x, y, size, YELLOW)
            arcade.draw_circle_filled(x + 15, y, size, LIME)

        for i, pacman in enumerate(self.pacmen):
            if pacman.power_mode:
                power_bar_width = 100
                power_bar_height = 8
                power_left = pacman.power_timer / pacman.power_duration
                x_pos = window.width // 4 + i * window.width // 2
                y_pos = window.height - 60

                outline_rect = arcade.rect.XYWH(x_pos, y_pos, power_bar_width, power_bar_height)
                arcade.draw_rect_outline(outline_rect, pacman.color, border_width=2)

                fill_width = power_bar_width * power_left
                if fill_width > 0:
                    fill_rect = arcade.rect.XYWH(x_pos - power_bar_width // 2 + fill_width // 2, y_pos, fill_width,
                                                 power_bar_height)
                    arcade.draw_rect_filled(fill_rect, BLUE if pacman.power_mode else pacman.color)

        arcade.draw_text(f"{self.player1_name}: ARROWS", 10, 30, YELLOW, 16)
        arcade.draw_text(f"{self.player2_name}: WASD", 10, 10, LIME, 16)
        arcade.draw_text("P: Пауза  R: Начать заново  ESC: Выход", window.width - 250, 20, WHITE, 16)

        if self.paused:
            center_x = window.width // 2
            center_y = window.height // 2
            width = 400
            height = 150
            pause_rect = arcade.rect.XYWH(center_x, center_y, width, height)
            arcade.draw_rect_filled(pause_rect, (0, 0, 0, 200))
            arcade.draw_text("Пауза", window.width // 2 - 60, window.height // 2 + 20,
                             arcade.color.YELLOW, 48, bold=True)
            arcade.draw_text("Нажмите P чтобы продолжить", window.width // 2 - 100,
                             window.height // 2 - 30, WHITE, 24)

        if self.game_over:
            center_x = window.width // 2
            center_y = window.height // 2
            width = 500
            height = 200
            game_over_rect = arcade.rect.XYWH(center_x, center_y, width, height)
            arcade.draw_rect_filled(game_over_rect, (0, 0, 0, 230))
            arcade.draw_text("ИГРА ОКОНЧЕНА!", window.width // 2 - 120,
                             window.height // 2 + 40, arcade.color.RED, 48, bold=True)
            arcade.draw_text(f"Итоговый счет: {self.total_score} ({self.total_score // 100}🪙)", window.width // 2 - 100,
                             window.height // 2 - 20, WHITE, 28)
            arcade.draw_text("Нажмите ESC для выхода", window.width // 2 - 100,
                             window.height // 2 - 60, arcade.color.YELLOW, 24)

        if self.game_won:
            center_x = window.width // 2
            center_y = window.height // 2
            width = 500
            height = 200
            victory_rect = arcade.rect.XYWH(center_x, center_y, width, height)
            arcade.draw_rect_filled(victory_rect, (0, 0, 0, 230))
            arcade.draw_text("Победа!", window.width // 2 - 100,
                             window.height // 2 + 40, arcade.color.GREEN, 48, bold=True)
            arcade.draw_text(f"Итоговый счет: {self.total_score} ({self.total_score // 100}🪙)", window.width // 2 - 80,
                             window.height // 2 - 10, WHITE, 32)
            arcade.draw_text("Нажмите ESC для выхода", window.width // 2 - 120,
                             window.height // 2 - 40, arcade.color.YELLOW, 28)

    def on_update(self, delta_time):
        if self.paused or self.game_over or self.game_won or not self.game_started:
            return

        self.frame_count += 1

        for pacman in self.pacmen:
            pacman.update()
            pacman.move()

            if pacman.alive:
                grid_x = int(pacman.center_x // CELL_SIZE)
                grid_y = GRID_HEIGHT - 1 - int(pacman.center_y // CELL_SIZE)

                for dot in self.dots[:]:
                    if dot[0] == grid_x and dot[1] == grid_y:
                        self.dots.remove(dot)
                        pacman.score += 10
                        self.total_score += 10
                        break

                for energizer in self.energizers[:]:
                    if energizer[0] == grid_x and energizer[1] == grid_y:
                        self.energizers.remove(energizer)
                        pacman.score += 50
                        self.total_score += 50
                        pacman.activate_power()

                        for ghost in self.ghosts:
                            ghost.activate_frightened()
                        break

        for ghost in self.ghosts:
            ghost.update()
            ghost.choose_direction(self.pacmen, self.ghosts)
            ghost.move()

        for ghost in self.ghosts:
            for pacman in self.pacmen:
                if pacman.alive and not pacman.respawning:
                    distance = ((pacman.center_x - ghost.center_x) ** 2 +
                                (pacman.center_y - ghost.center_y) ** 2) ** 0.5

                    if distance < pacman.radius + ghost.radius:
                        if ghost.frightened and not ghost.eyes_only:
                            ghost.die()
                            pacman.score += 200
                            self.total_score += 200
                        elif not ghost.eyes_only:
                            pacman.die()

                            alive_pacmen = [p for p in self.pacmen if p.alive]
                            if not alive_pacmen:
                                self.shared_lives -= 1
                                if self.shared_lives <= 0:
                                    self.game_over = True
                                else:
                                    for i, p in enumerate(self.pacmen):
                                        p.respawn(13 + i, 23)
                                    for ghost in self.ghosts:
                                        ghost.respawn()

        if len(self.dots) == 0 and len(self.energizers) == 0:
            self.game_won = True

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            if not self.game_started:
                self.game_started = True

        if key == arcade.key.ESCAPE:
            from Game_windows import ChooseGame
            if self.game_over or self.game_won:
                self.cursor.execute(
                    f"""UPDATE data_players SET value = value + {self.total_score // 100} WHERE id = 0""")
                self.conn.commit()
            self.window.show_view(ChooseGame())


        if key == arcade.key.P:
            self.paused = not self.paused

        if (self.game_over or self.game_won) and key == arcade.key.R:
            self.setup()
            return

        if key == arcade.key.UP:
            self.pacman1.set_direction(Direction.UP)
        elif key == arcade.key.DOWN:
            self.pacman1.set_direction(Direction.DOWN)
        elif key == arcade.key.LEFT:
            self.pacman1.set_direction(Direction.LEFT)
        elif key == arcade.key.RIGHT:
            self.pacman1.set_direction(Direction.RIGHT)

        if key == arcade.key.W:
            self.pacman2.set_direction(Direction.UP)
        elif key == arcade.key.S:
            self.pacman2.set_direction(Direction.DOWN)
        elif key == arcade.key.A:
            self.pacman2.set_direction(Direction.LEFT)
        elif key == arcade.key.D:
            self.pacman2.set_direction(Direction.RIGHT)

    def on_key_release(self, key, modifiers):
        pass


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_view = PacManGame()
    window.show_view(game_view)
    arcade.run()


if __name__ == "__main__":
    main()