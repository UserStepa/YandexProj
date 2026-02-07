import arcade
import random
import sqlite3

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650
GAME_TIME = 60

BRICK_ROWS = 6
BRICK_COLUMNS = 8
BRICK_WIDTH = SCREEN_WIDTH // BRICK_COLUMNS - 1
BRICK_HEIGHT = 30
BRICK_COLORS = [
    arcade.color.RED,
    arcade.color.ORANGE,
    arcade.color.YELLOW,
    arcade.color.GREEN,
    arcade.color.BLUE,
    arcade.color.VIOLET
]


class Ball(arcade.Sprite):
    def __init__(self, texture, scale):
        super().__init__(texture, scale)
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = 30
        self.change_x = 0
        self.change_y = 0
        self.speed = 400

    def setup(self):
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = 30
        self.change_x = random.uniform(-50, 50)
        self.change_y = self.speed

    def update(self, delta_time):
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time

        if self.left <= 0 or self.right >= SCREEN_WIDTH:
            self.change_x *= -1

        if self.top >= SCREEN_HEIGHT:
            self.change_y *= -1


class Paddle(arcade.Sprite):
    def __init__(self, texture, scale):
        super().__init__(texture, scale)
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = 20
        self.speed = 400

    def update(self, delta_time):
        if self.left < 0:
            self.left = 0
        elif self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH


class Brick(arcade.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.center_x = x + width / 2
        self.center_y = y + height / 2
        self.width = width
        self.height = height
        self.color = color
        self.texture = arcade.make_soft_square_texture(width, color, outer_alpha=200)

    def draw(self):
        arcade.draw_lbwh_rectangle_filled(
            self.left, self.bottom, self.width, self.height, self.color
        )


class ArkanoidGame(arcade.View):
    def __init__(self):
        super().__init__()

        self.background_color = arcade.color.BLACK
        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        self.player1_name = self.load_player_name(1)
        self.player2_name = self.load_player_name(2)

        self.score = 0
        self.time_left = GAME_TIME
        self.game_started = False
        self.game_over = False

        # Флаги для управления
        self.left_pressed = False
        self.right_pressed = False

        # Списки спрайтов
        self.ball = None
        self.paddle = None
        self.bricks = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()

        # Текстуры
        self.background = None
        self.ball_texture = None
        self.paddle_texture = None

        self.setup()

    def setup(self):
        # Купленный дизайн
        self.cursor.execute("SELECT value FROM data_players WHERE id = 3")
        result = self.cursor.fetchone()
        if result and result[0] == 1:
            self.ball = Ball("images/arcanoid/ball_designer.png", 0.08)
        else:
            self.ball = Ball("images/arcanoid/ball.png", 0.2)

        self.paddle_texture = arcade.load_texture("images/arcanoid/paddle.png")

        self.score = 0
        self.time_left = GAME_TIME
        self.game_started = False
        self.game_over = False
        self.left_pressed = False
        self.right_pressed = False

        self.bricks.clear()
        self.all_sprites.clear()

        self.ball.setup()
        self.all_sprites.append(self.ball)

        self.paddle = Paddle(self.paddle_texture, 0.2)
        self.all_sprites.append(self.paddle)

        for row in range(BRICK_ROWS):
            color = BRICK_COLORS[row % len(BRICK_COLORS)]
            for col in range(BRICK_COLUMNS):
                brick = Brick(
                    col * (BRICK_WIDTH + 1),
                    SCREEN_HEIGHT - (row + 1) * (BRICK_HEIGHT + 1),
                    BRICK_WIDTH, BRICK_HEIGHT, color
                )
                self.bricks.append(brick)
                self.all_sprites.append(brick)

    def load_player_name(self, player_id):
        self.cursor.execute(f"SELECT name FROM data_player{player_id} WHERE id = 0")
        result = self.cursor.fetchone()
        return result[0] if result else f"Игрок {player_id}"

    def on_draw(self):
        self.clear()

        # Отображение инструкции перед началом игры
        if not self.game_started and not self.game_over:
            arcade.draw_text("Выбивайте кирпичи и удерживайте шар!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100,
                             arcade.color.WHITE, 24, anchor_x="center")
            arcade.draw_text(f"Управление: {self.player1_name} - влево(A), {self.player2_name} - вправо(⟶)",
                             SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                             arcade.color.WHITE, 20, anchor_x="center")
            arcade.draw_text("Нажмите SPACE чтобы начать, ESC чтобы выйти",
                             SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                             arcade.color.WHITE, 20, anchor_x="center")
            return

        # Отображение результатов по окончании игры
        if self.game_over:
            arcade.draw_text("ИГРА ОКОНЧЕНА!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100,
                             arcade.color.WHITE, 36, anchor_x="center")
            arcade.draw_text(f"Итоговый счет: {self.score}🪙", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                             arcade.color.GOLD, 28, anchor_x="center")
            arcade.draw_text("Нажмите ESC чтобы выйти", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                             arcade.color.WHITE, 20, anchor_x="center")
            return

        self.all_sprites.draw()

        arcade.draw_text(f"Счет: {self.score}", 10, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 24)

        minutes = int(self.time_left) // 60
        seconds = int(self.time_left) % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        arcade.draw_text(time_text, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 24)

    def on_update(self, delta_time):
        if not self.game_started or self.game_over:
            return

        # Обновление времени
        self.time_left -= delta_time
        if self.time_left <= 0:
            self.time_left = 0
            self.game_over = True
            return

        # Управление платформой
        if self.left_pressed and not self.right_pressed:
            self.paddle.center_x -= self.paddle.speed * delta_time
        elif self.right_pressed and not self.left_pressed:
            self.paddle.center_x += self.paddle.speed * delta_time

        # Обновление
        self.paddle.update(delta_time)
        self.ball.update(delta_time)

        # Проверка столкновения мяча с платформой
        if arcade.check_for_collision(self.ball, self.paddle):
            hit_pos = (self.ball.center_x - self.paddle.center_x) / self.paddle.width
            self.ball.change_x = hit_pos * self.ball.speed * 2
            self.ball.change_y *= -1
            self.ball.bottom = self.paddle.top

        # Проверка столкновения мяча с кирпичами
        hit_list = arcade.check_for_collision_with_list(self.ball, self.bricks)
        if hit_list:
            for brick in hit_list:
                self.bricks.remove(brick)
                self.all_sprites.remove(brick)
                self.score += 1
            self.ball.change_y *= -1

        if self.ball.bottom <= 0:
            self.game_over = True

        if len(self.bricks) == 0:
            self.game_over = True

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            if not self.game_started:
                self.game_started = True

        if key == arcade.key.ESCAPE:
            if self.game_over:
                self.cursor.execute("UPDATE data_players SET value = value + ? WHERE id = 0", (self.score,))
                self.conn.commit()

            from Game_windows import ChooseGame
            self.window.show_view(ChooseGame())

        if key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Arkanoid Game")
    game_view = ArkanoidGame()
    window.show_view(game_view)
    arcade.run()


if __name__ == "__main__":
    main()