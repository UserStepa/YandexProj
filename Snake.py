import arcade
import random
import sqlite3

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650
GRID_SIZE = 20
CELL_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // CELL_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // CELL_SIZE
FOOD_COUNT = 3

BACKGROUND_COLOR = arcade.color.BLACK
GRID_COLOR = arcade.color.DARK_SLATE_GRAY
PLAYER1_COLOR = arcade.color.GREEN
PLAYER2_COLOR = arcade.color.BLUE
PLAYER1_HEAD = arcade.color.LIME_GREEN
PLAYER2_HEAD = arcade.color.CYAN
FOOD_COLOR = arcade.color.RED
TEXT_COLOR = arcade.color.WHITE


class Snake:
    def __init__(self, x: int, y: int, color: tuple, controls: dict, player_num: int, name: str = ""):
        self.segments = [(x, y)]
        self.color = color
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.grow_pending = 0
        self.controls = controls
        self.player_num = player_num
        self.name = name if name else f"Игрок {player_num}"
        self.score = 0
        self.alive = True

    def change_direction(self, direction: tuple):
        dx, dy = direction
        current_dx, current_dy = self.direction
        if (dx, dy) != (-current_dx, -current_dy):
            self.next_direction = direction

    def update(self):
        if not self.alive:
            return
        self.direction = self.next_direction
        head_x, head_y = self.segments[0]
        dx, dy = self.direction
        new_head_x = (head_x + dx) % GRID_WIDTH
        new_head_y = (head_y + dy) % GRID_HEIGHT
        if (new_head_x, new_head_y) in self.segments:
            self.alive = False
            return
        self.segments.insert(0, (new_head_x, new_head_y))
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.segments.pop()

    def grow(self):
        self.grow_pending += 1

    def draw(self):
        for i, (x, y) in enumerate(self.segments):
            if i == 0:
                if self.player_num == 1:
                    color = PLAYER1_HEAD
                else:
                    color = PLAYER2_HEAD
            else:
                color = self.color
            pos_x = x * CELL_SIZE
            pos_y = y * CELL_SIZE
            arcade.draw_lrbt_rectangle_filled(
                left=pos_x + 1,
                right=pos_x + CELL_SIZE - 1,
                top=pos_y + CELL_SIZE - 1,
                bottom=pos_y + 1,
                color=color
            )
            if i == 0 and self.alive:
                eye_size = 3
                dx, dy = self.direction
                if dx == 1:
                    arcade.draw_circle_filled(
                        center_x=pos_x + CELL_SIZE - 5,
                        center_y=pos_y + 13,
                        radius=eye_size,
                        color=arcade.color.WHITE
                    )
                    arcade.draw_circle_filled(
                        center_x=pos_x + CELL_SIZE - 5,
                        center_y=pos_y + 7,
                        radius=eye_size,
                        color=arcade.color.WHITE
                    )
                elif dx == -1:
                    arcade.draw_circle_filled(
                        center_x=pos_x + 5,
                        center_y=pos_y + 13,
                        radius=eye_size,
                        color=arcade.color.WHITE
                    )
                    arcade.draw_circle_filled(
                        center_x=pos_x + 5,
                        center_y=pos_y + 7,
                        radius=eye_size,
                        color=arcade.color.WHITE
                    )
                elif dy == 1:
                    arcade.draw_circle_filled(
                        center_x=pos_x + 7,
                        center_y=pos_y + CELL_SIZE - 5,
                        radius=eye_size,
                        color=arcade.color.WHITE
                    )
                    arcade.draw_circle_filled(
                        center_x=pos_x + 13,
                        center_y=pos_y + CELL_SIZE - 5,
                        radius=eye_size,
                        color=arcade.color.WHITE
                    )
                elif dy == -1:
                    arcade.draw_circle_filled(
                        center_x=pos_x + 7,
                        center_y=pos_y + 5,
                        radius=eye_size,
                        color=arcade.color.WHITE
                    )
                    arcade.draw_circle_filled(
                        center_x=pos_x + 13,
                        center_y=pos_y + 5,
                        radius=eye_size,
                        color=arcade.color.WHITE
                    )


class Food:
    def __init__(self):
        self.position = (0, 0)
        self.respawn([])

    def respawn(self, snakes):
        occupied = set()
        for snake in snakes:
            occupied.update(snake.segments)
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in occupied:
                self.position = (x, y)
                break

    def draw(self):
        x, y = self.position
        pos_x = x * CELL_SIZE
        pos_y = y * CELL_SIZE
        arcade.draw_circle_filled(
            center_x=pos_x + CELL_SIZE // 2,
            center_y=pos_y + CELL_SIZE // 2,
            radius=CELL_SIZE // 2 - 3,
            color=FOOD_COLOR
        )
        arcade.draw_line(
            start_x=pos_x + CELL_SIZE // 2,
            start_y=pos_y + CELL_SIZE,
            end_x=pos_x + CELL_SIZE // 2 + 3,
            end_y=pos_y + CELL_SIZE + 5,
            color=arcade.color.DARK_GREEN,
            line_width=2
        )
        arcade.draw_triangle_filled(
            x1=pos_x + CELL_SIZE // 2,
            y1=pos_y + CELL_SIZE,
            x2=pos_x + CELL_SIZE // 2 + 8,
            y2=pos_y + CELL_SIZE - 3,
            x3=pos_x + CELL_SIZE // 2 + 3,
            y3=pos_y + CELL_SIZE + 3,
            color=arcade.color.GREEN
        )


class SnakeGame(arcade.View):
    def __init__(self):
        super().__init__()

        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        self.player1_name = self.load_player_name(1)
        self.player2_name = self.load_player_name(2)

        self.player1_texture = self.load_player_texture(1)
        self.player2_texture = self.load_player_texture(2)

        self.snake1 = None
        self.snake2 = None
        self.snakes = []
        self.foods = [Food() for _ in range(FOOD_COUNT)]
        self.game_over = False
        self.game_started = False
        self.winner = None
        self.winner_id = 0
        self.game_speed = 10
        self.frame_count = 0

        self.score_text1 = arcade.Text(
            "",
            80, SCREEN_HEIGHT - 30,
            PLAYER1_HEAD, 20
        )
        self.score_text2 = arcade.Text(
            "",
            SCREEN_WIDTH - 200, SCREEN_HEIGHT - 30,
            PLAYER2_HEAD, 20
        )
        self.game_over_text = arcade.Text(
            "",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            TEXT_COLOR, 48,
            align="center", anchor_x="center", anchor_y="center"
        )
        self.restart_text = arcade.Text(
            "Нажмите ESC для выхода в меню",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100,
            TEXT_COLOR, 20,
            align="center", anchor_x="center", anchor_y="center"
        )

    def load_player_name(self, player_id):
        self.cursor.execute(f"SELECT name FROM data_player{player_id} WHERE id = 0")
        result = self.cursor.fetchone()
        return result[0] if result else f"Игрок {player_id}"


    def load_player_texture(self, player_id):
        self.cursor.execute(f"SELECT name FROM data_player{player_id} WHERE value = 1")
        result = self.cursor.fetchone()
        if result:
            return arcade.load_texture(f"images/data_player{player_id}/{result[0]}.png")


    def start_game(self):
        self.snake1 = Snake(
            x=GRID_WIDTH // 4,
            y=GRID_HEIGHT // 2,
            color=PLAYER1_COLOR,
            controls={
                arcade.key.W: (0, 1),
                arcade.key.S: (0, -1),
                arcade.key.A: (-1, 0),
                arcade.key.D: (1, 0)
            },
            player_num=1,
            name=self.player1_name
        )
        self.snake2 = Snake(
            x=3 * GRID_WIDTH // 4,
            y=GRID_HEIGHT // 2,
            color=PLAYER2_COLOR,
            controls={
                arcade.key.UP: (0, 1),
                arcade.key.DOWN: (0, -1),
                arcade.key.LEFT: (-1, 0),
                arcade.key.RIGHT: (1, 0)
            },
            player_num=2,
            name=self.player2_name
        )
        self.snakes = [self.snake1, self.snake2]
        for food in self.foods:
            food.respawn(self.snakes)
        self.score_text1.text = f"{self.snake1.name}: {self.snake1.score}"
        self.score_text2.text = f"{self.snake2.name}: {self.snake2.score}"
        self.game_started = True

    def on_draw(self):
        self.clear(BACKGROUND_COLOR)

        if not self.game_started and not self.game_over:
            arcade.draw_text("Ешьте яблоки и выживайте на одном поле!",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100, arcade.color.GOLD, 30, anchor_x="center")
            arcade.draw_text("Нажмите: Space - чтобы начать, Esc - чтобы выйти",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, arcade.color.WHITE, 20, anchor_x="center")

            if self.player1_texture:
                arcade.draw_texture_rect(self.player1_texture, arcade.rect.XYWH(
                    SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 100, 80, 80))
            arcade.draw_text(f'{self.player1_name} (WASD)',
                             SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 200,
                             PLAYER1_HEAD, 20, anchor_x="center")

            if self.player2_texture:
                arcade.draw_texture_rect(self.player2_texture, arcade.rect.XYWH(
                    SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 - 100, 80, 80))
            arcade.draw_text(f'{self.player2_name} (↑↓←→)',
                             SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 - 200,
                             PLAYER2_HEAD, 20, anchor_x="center")

            return

        self._draw_grid()
        for food in self.foods:
            food.draw()
        for snake in self.snakes:
            snake.draw()
        self._draw_ui()

        if self.game_over:
            self._draw_game_over()

    def _draw_grid(self):
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            arcade.draw_line(
                start_x=x,
                start_y=0,
                end_x=x,
                end_y=SCREEN_HEIGHT,
                color=GRID_COLOR,
                line_width=1
            )
        for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
            arcade.draw_line(
                start_x=0,
                start_y=y,
                end_x=SCREEN_WIDTH,
                end_y=y,
                color=GRID_COLOR,
                line_width=1
            )

    def _draw_ui(self):
        if self.snake1:
            self.score_text1.text = f"{self.snake1.name}: {self.snake1.score}"
        if self.snake2:
            self.score_text2.text = f"{self.snake2.name}: {self.snake2.score}"

        self.score_text1.draw()
        self.score_text2.draw()

        if self.player1_texture:
            arcade.draw_texture_rect(self.player1_texture, arcade.rect.XYWH(
                45, SCREEN_HEIGHT - 25, 50, 50))

        if self.player2_texture:
            arcade.draw_texture_rect(self.player2_texture, arcade.rect.XYWH(
                SCREEN_WIDTH - 30, SCREEN_HEIGHT - 25, 50, 50))

        arcade.draw_text(
            f"Яблок на поле: {FOOD_COUNT}",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80,
            arcade.color.GOLD, 18,
            align="center", anchor_x="center"
        )

        status_y = SCREEN_HEIGHT - 120
        if self.snake1 and not self.snake1.alive:
            arcade.draw_text(
                "МЕРТВ",
                SCREEN_WIDTH // 2 - 150, status_y,
                arcade.color.RED, 16
            )
        if self.snake2 and not self.snake2.alive:
            arcade.draw_text(
                "МЕРТВ",
                SCREEN_WIDTH // 2 + 150, status_y,
                arcade.color.RED, 16
            )

    def _draw_game_over(self):
        if self.winner == 1:
            message = f"Игра закончена! Победил {self.player1_name} (+10🪙)"
            color = PLAYER1_HEAD
        elif self.winner == 2:
            message = f"Игра закончена! Победил {self.player2_name} (+10🪙)"
            color = PLAYER2_HEAD
        elif self.winner == 0:
            message = "Ничья!"
            color = TEXT_COLOR
        else:
            message = "Игра окончена!"
            color = TEXT_COLOR

        arcade.draw_text(message,
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100, arcade.color.GOLD, 30, anchor_x="center")
        arcade.draw_text("Нажмите Esc чтобы вернуться в меню",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, arcade.color.WHITE, 20, anchor_x="center")

    def on_update(self, delta_time: float):
        if not self.game_started or self.game_over:
            return

        self.frame_count += 1
        if self.frame_count >= self.game_speed:
            self.frame_count = 0
            for snake in self.snakes:
                if snake.alive:
                    snake.update()
            self._check_collisions_between_snakes()
            self._check_food_collision()
            self._check_game_over()

    def _check_collisions_between_snakes(self):
        for snake in self.snakes:
            if snake.alive and len(snake.segments) > 0:
                head = snake.segments[0]
                for other_snake in self.snakes:
                    if other_snake != snake and other_snake.alive:
                        if head in other_snake.segments:
                            snake.alive = False
                            break

    def _check_food_collision(self):
        for snake in self.snakes:
            if snake.alive and len(snake.segments) > 0:
                head_x, head_y = snake.segments[0]
                for food in self.foods:
                    food_x, food_y = food.position
                    if head_x == food_x and head_y == food_y:
                        snake.grow()
                        snake.score += 10
                        if self.game_speed > 5:
                            self.game_speed -= 0.2
                        food.respawn(self.snakes)
                        break

    def _check_game_over(self):
        alive_snakes = [snake for snake in self.snakes if snake.alive]
        if len(alive_snakes) == 0:
            self.game_over = True
            self.winner = 0
        elif len(alive_snakes) == 1:
            self.game_over = True
            self.winner = alive_snakes[0].player_num
            self.winner_id = alive_snakes[0].player_num
            if self.winner_id:
                self.cursor.execute(f"""UPDATE data_player{self.winner_id} 
                SET value = value + 10 WHERE id = 0""")
                self.conn.commit()

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.ESCAPE:
            from Game_windows import ChooseGame
            self.window.show_view(ChooseGame())
            return

        if not self.game_started and not self.game_over:
            if key == arcade.key.SPACE:
                self.start_game()
            return

        for snake in self.snakes:
            if key in snake.controls:
                snake.change_direction(snake.controls[key])


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT)
    snake_game = SnakeGame()
    window.show_view(snake_game)
    arcade.run()


if __name__ == "__main__":
    main()