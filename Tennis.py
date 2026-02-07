import arcade
import sqlite3
import random
import math

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650

PADDLE_WIDTH = 10
PADDLE_COLOR = arcade.color.WHITE
PADDLE_SPEED = 80
PADDLE_SCALE = 0.3

BALL_SPEED = 200


class Ball(arcade.Sprite):
    def __init__(self, texture_ball, scale):
        super().__init__(texture_ball, scale)
        self.reset()

    def reset(self):
        self.center_x = SCREEN_WIDTH / 2
        self.center_y = SCREEN_HEIGHT / 2

        angle = random.uniform(30, 60)
        if random.choice([True, False]):
            angle = -angle

        radians = math.radians(angle)
        self.change_x = BALL_SPEED * math.cos(radians)
        self.change_y = BALL_SPEED * math.sin(radians)

    def update(self, delta_time):
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time

        if self.top >= SCREEN_HEIGHT or self.bottom <= 0:
            self.change_y *= -1


class Paddle(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__("images/tennis/paddle.png", PADDLE_SCALE)
        self.width = PADDLE_WIDTH
        self.height = 100
        self.color = PADDLE_COLOR
        self.center_x = x
        self.center_y = y

    def move_up(self):
        self.center_y += PADDLE_SPEED

    def move_down(self):
        self.center_y -= PADDLE_SPEED

    def update(self, delta_time):
        if self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT
        if self.bottom < 0:
            self.bottom = 0


class TennisGame(arcade.View):
    def __init__(self):
        super().__init__()

        self.texture = arcade.load_texture("images/tennis/tennis_table.png")

        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        self.player1_name = self.load_player_name(1)
        self.player2_name = self.load_player_name(2)

        # Звуки отскока мяча
        self.paddle_hit_sound = arcade.load_sound(":resources:sounds/hit5.wav")
        self.wall_hit_sound = arcade.load_sound(":resources:sounds/hit4.wav")
        self.score_sound = arcade.load_sound(":resources:sounds/upgrade4.wav")
        self.start_sound = arcade.load_sound(":resources:sounds/coin2.wav")

        # Купленный дизайн
        self.cursor.execute("SELECT value FROM data_players WHERE id = 1")
        result = self.cursor.fetchone()
        if result[0] == 1:
            self.ball = Ball("images/tennis/ball_designer.png", 0.075)
        else:
            self.ball = Ball("images/tennis/ball.png", 0.2)

        self.player1_texture = self.load_texture("data_player1", 1)
        self.player2_texture = self.load_texture("data_player2", 2)

        self.left_paddle = Paddle(PADDLE_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.right_paddle = Paddle(SCREEN_WIDTH - PADDLE_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.sprite_list = arcade.SpriteList()

        self.left_score = 0
        self.right_score = 0

        self.game_over = False
        self.game_started = False

        self.winner = None
        self.winner_id = 0

        self.setup()

    def load_player_name(self, player_id):
        self.cursor.execute(f"SELECT name FROM data_player{player_id} WHERE id = 0")
        result = self.cursor.fetchone()
        return result[0] if result else f"Игрок {player_id}"

    def load_texture(self, name, id):
        self.cursor.execute(
            f"SELECT name FROM {name} WHERE value = 1")
        result = self.cursor.fetchone()
        texture = arcade.load_texture(f"images/data_player{id}/{result[0]}.png")
        return texture

    def setup(self):
        self.sprite_list.append(self.ball)
        self.sprite_list.append(self.left_paddle)
        self.sprite_list.append(self.right_paddle)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.sprite_list.draw()

        # Аватары
        arcade.draw_texture_rect(self.player1_texture, arcade.rect.XYWH(
            SCREEN_WIDTH // 2 - 65, SCREEN_HEIGHT - 40,50, 50))

        arcade.draw_texture_rect(self.player2_texture, arcade.rect.XYWH(
            SCREEN_WIDTH // 2 + 65, SCREEN_HEIGHT - 40, 50, 50))

        score_text = f"{self.left_score} - {self.right_score}"
        arcade.draw_text(score_text, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40,
        arcade.color.WHITE,24, anchor_x="center")

        if not self.game_started and not self.game_over:
            arcade.draw_text("Забейте 5 раз сопернику!",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150, arcade.color.BLACK, 20, anchor_x="center")
            arcade.draw_text("Нажмите: Space - чтобы начать, Esc - чтобы выйти",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100, arcade.color.BLACK, 20, anchor_x="center")
            arcade.draw_text(f"Управление: {self.player1_name} - WS, {self.player2_name} - ↑↓",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, arcade.color.BLACK, 20, anchor_x="center")

        if self.game_over:
            arcade.draw_text(f"Игра закончена! Победил {self.winner} (+10🪙)",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100, arcade.color.GOLD, 30, anchor_x="center")
            arcade.draw_text(f"Нажмите Esc чтобы вернуться в меню",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, arcade.color.WHITE, 20, anchor_x="center")

    def on_update(self, delta_time):
        if not self.game_started or self.game_over:
            return

        self.sprite_list.update(delta_time)
        self.ball.update(delta_time)

        # Проверка столкновения с верхней/нижней стенкой
        if self.ball.top >= SCREEN_HEIGHT or self.ball.bottom <= 0:
            arcade.play_sound(self.wall_hit_sound, volume=0.3)

        # Проверка столкновения с левой ракеткой
        if arcade.check_for_collision(self.ball, self.left_paddle):
            arcade.play_sound(self.paddle_hit_sound, volume=0.5)
            self.ball.change_x = abs(self.ball.change_x)
            self.ball.left = self.left_paddle.right

        # Проверка столкновения с правой ракеткой
        if arcade.check_for_collision(self.ball, self.right_paddle):
            arcade.play_sound(self.paddle_hit_sound, volume=0.5)
            self.ball.change_x = -abs(self.ball.change_x)
            self.ball.right = self.right_paddle.left

        # Проверка гола
        if self.ball.left <= 0:
            self.right_score += 1
            arcade.play_sound(self.score_sound, volume=0.5)
            self.ball.reset()
            self.game_started = False
        elif self.ball.right >= SCREEN_WIDTH:
            self.left_score += 1
            arcade.play_sound(self.score_sound, volume=0.5)
            self.ball.reset()
            self.game_started = False

        if self.left_score == 5:
            self.game_over = True
            self.winner = self.player1_name
            self.winner_id = 1
        elif self.right_score == 5:
            self.game_over = True
            self.winner = self.player2_name
            self.winner_id = 2

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            if not self.game_started and not self.game_over:
                self.game_started = True
                arcade.play_sound(self.start_sound, volume=0.5)
                self.ball.reset()

        if key == arcade.key.ESCAPE:
            from Game_windows import ChooseGame
            if self.game_over:
                self.cursor.execute(f"""UPDATE data_player{self.winner_id} 
                SET value = value + 10 WHERE id = 0""")
                self.conn.commit()
            self.window.show_view(ChooseGame())

        if key == arcade.key.W:
            self.left_paddle.move_up()
        elif key == arcade.key.S:
            self.left_paddle.move_down()

        elif key == arcade.key.UP:
            self.right_paddle.move_up()
        elif key == arcade.key.DOWN:
            self.right_paddle.move_down()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT)
    game_view = TennisGame()
    window.show_view(game_view)
    arcade.run()


if __name__ == "__main__":
    main()