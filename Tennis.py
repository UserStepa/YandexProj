import os
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

BALL_SCALE = 0.2
BALL_SPEED = 200

class Ball(arcade.Sprite):
    def __init__(self, scale):
        super().__init__("images/tennis/ball.png", scale)
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

        self.ball = Ball(BALL_SCALE)
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

    def setup(self):
        self.sprite_list.append(self.ball)
        self.sprite_list.append(self.left_paddle)
        self.sprite_list.append(self.right_paddle)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.sprite_list.draw()

        score_text = f"{self.left_score} - {self.right_score}"
        arcade.draw_text(score_text, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40,
        arcade.color.WHITE,24, anchor_x="center")

        if not self.game_started and not self.game_over:
            arcade.draw_text("Забейте 5 раз сопернику!",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100, arcade.color.BLACK, 20, anchor_x="center")
            arcade.draw_text("Нажмите: Space - чтобы начать, Esc - чтобы выйти",
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

        if arcade.check_for_collision(self.ball, self.left_paddle):
            self.ball.change_x *= -1
            self.ball.left = self.left_paddle.right

        if arcade.check_for_collision(self.ball, self.right_paddle):
            self.ball.change_x *= -1
            self.ball.right = self.right_paddle.left

        if self.ball.left <= 0:
            self.right_score += 1
            self.ball.reset()
            self.game_started = False
        elif self.ball.right >= SCREEN_WIDTH:
            self.left_score += 1
            self.ball.reset()
            self.game_started = False

        if self.left_score == 5:
            self.game_over = True
            self.cursor.execute("SELECT name FROM data_player1 WHERE id = 1",)
            result = self.cursor.fetchone()
            self.winner = result[0]
            self.winner_id = 1
        elif self.right_score == 5:
            self.game_over = True
            self.cursor.execute("SELECT name FROM data_player2 WHERE id = 2")
            result = self.cursor.fetchone()
            self.winner = result[0]
            self.winner_id = 2


    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            if not self.game_started:
                self.game_started = True
                self.ball.reset()

        if key == arcade.key.ESCAPE:
            from Game_windows import ChooseGame
            if self.game_over:
                self.cursor.execute(f"""UPDATE data_player{self.winner_id} 
                SET bank = bank + ? WHERE id = ?""", (10, self.winner_id))
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