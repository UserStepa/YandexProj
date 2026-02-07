import arcade
import random
import math
import sqlite3

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650


class Ball(arcade.Sprite):
    def __init__(self, texture, scale, x, y):
        super().__init__(texture, scale)
        self.in_pocket = False
        self.velocity_x = 0
        self.velocity_y = 0
        self.center_x = x
        self.center_y = y

    def update(self):
        self.velocity_x *= 0.98
        self.velocity_y *= 0.98

        if abs(self.velocity_x) < 0.1:
            self.velocity_x = 0
        if abs(self.velocity_y) < 0.1:
            self.velocity_y = 0

        self.center_x += self.velocity_x
        self.center_y += self.velocity_y

        # Отскок от границ
        if self.center_x < 60 or self.center_x > SCREEN_WIDTH - 60:
            self.velocity_x *= -0.9
        if self.center_y < 60 or self.center_y > SCREEN_HEIGHT - 60:
            self.velocity_y *= -0.9

        # Проверка на попадание в лузку
        if (self.center_x < 30 or self.center_x > SCREEN_WIDTH - 30 or
                self.center_y < 30 or self.center_y > SCREEN_HEIGHT - 30):
            self.in_pocket = True

    def is_stopped(self):
        return self.velocity_x == 0 and self.velocity_y == 0


class GolfGame(arcade.View):
    def __init__(self):
        super().__init__()

        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        self.name_1 = 'Игрок 1'
        self.name_2 = 'Игрок 2'
        self.game_time = 60
        self.time_left = self.game_time
        self.score = 0
        self.player_turn = 1

        self.background = None
        self.ball = None
        self.pocket = None

        self.ball_sprites = arcade.SpriteList()
        self.pocket_sprites = arcade.SpriteList()
        self.flag_sprites = arcade.SpriteList()

        self.game_state = "AIMING"
        self.game_started = False
        self.aim_angle = 0
        self.aim_direction = 1
        self.power = 0
        self.power_direction = 1
        self.selected_angle = 0

        self.key_w_pressed = False
        self.key_up_pressed = False

        self.setup()

    def setup(self):
        self.cursor.execute("SELECT name FROM data_player1 WHERE id = 0")
        result = self.cursor.fetchone()
        self.name_1 = result[0]

        self.cursor.execute("SELECT name FROM data_player2 WHERE id = 0")
        result = self.cursor.fetchone()
        self.name_2 = result[0]

        self.background = arcade.load_texture("images/golf/golf_background.png")

        self.create_random_positions()

        self.aim_angle = 0
        self.power = 0
        self.game_state = "AIMING"

    def create_random_positions(self):
        self.ball_sprites.clear()
        self.pocket_sprites.clear()
        self.flag_sprites.clear()

        ball_x = random.randint(100, SCREEN_WIDTH - 100)
        ball_y = random.randint(100, SCREEN_HEIGHT - 100)

        pocket_x = random.randint(100, SCREEN_WIDTH - 100)
        pocket_y = random.randint(100, SCREEN_HEIGHT - 100)

        while abs(pocket_x - ball_x) < 150 and abs(pocket_y - ball_y) < 150:
            pocket_x = random.randint(100, SCREEN_WIDTH - 100)
            pocket_y = random.randint(100, SCREEN_HEIGHT - 100)

        # Купленный дизайн
        self.cursor.execute("SELECT value FROM data_players WHERE id = 2")
        result = self.cursor.fetchone()
        if result[0] == 1:
            self.ball = Ball("images/golf/ball_designer.png", 0.075, ball_x, ball_y)
        else:
            self.ball = Ball("images/golf/ball.png", 0.25, ball_x, ball_y)
        self.ball_sprites.append(self.ball)

        self.pocket = arcade.Sprite("images/golf/pocket.png", scale=0.5)
        self.pocket.center_x = pocket_x
        self.pocket.center_y = pocket_y
        self.pocket_sprites.append(self.pocket)

        self.flag = arcade.Sprite("images/golf/flag.png", scale=0.2)
        self.flag.center_x = pocket_x
        self.flag.center_y = pocket_y + 45
        self.flag_sprites.append(self.flag)

    def on_draw(self):
        self.clear()

        if self.background:
            arcade.draw_texture_rect(self.background, arcade.rect.XYWH(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))

        if not self.game_started and self.game_state != "GAME_OVER":
            arcade.draw_text("Забивайте пока время не закончилось!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70,
                             arcade.color.BLACK, 32, bold=True, anchor_x="center")
            arcade.draw_text("Нажмите: Space - чтобы начать, Esc - чтобы выйти", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2, arcade.color.BLACK, 24, anchor_x="center")
            return

        self.pocket_sprites.draw()
        self.ball_sprites.draw()
        self.flag_sprites.draw()

        if self.game_state == "AIMING" and self.ball and not self.ball.in_pocket:
            distance = 80
            angle_rad = math.radians(self.aim_angle)

            end_x = self.ball.center_x + math.cos(angle_rad) * distance
            end_y = self.ball.center_y + math.sin(angle_rad) * distance

            arcade.draw_line(self.ball.center_x,
                             self.ball.center_y,
                             end_x, end_y,
                             arcade.color.RED, 3)

            arrow_size = 15
            left_angle = angle_rad + math.radians(150)
            right_angle = angle_rad - math.radians(150)

            left_x = end_x + math.cos(left_angle) * arrow_size
            left_y = end_y + math.sin(left_angle) * arrow_size
            right_x = end_x + math.cos(right_angle) * arrow_size
            right_y = end_y + math.sin(right_angle) * arrow_size

            arcade.draw_triangle_filled(end_x, end_y,
                                        left_x, left_y,
                                        right_x, right_y,
                                        arcade.color.RED)

        # Очки
        arcade.draw_text(f"Очки: {self.score}", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 28, bold=True, anchor_x="center")

        # Время
        minutes = int(self.time_left) // 60
        seconds = int(self.time_left) % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        arcade.draw_text(time_text, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70,
                         arcade.color.WHITE, 22, bold=True, anchor_x="center")

        # Смена игроков
        arcade.draw_text("Нажмите R чтобы поменяться", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 110,
                         arcade.color.LIGHT_BLUE, 16, bold=True, anchor_x="center")

        # Ход игрока
        if self.game_state != "GAME_OVER":
            if self.player_turn == 1:
                arcade.draw_text(f"{self.name_1}: Выберите направление (W)", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 145,
                                 arcade.color.YELLOW, 18, bold=True, anchor_x="center")
                arcade.draw_text(f"{self.name_2}: Выберите силу (↑)", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 175,
                                 arcade.color.LIGHT_GRAY, 16, anchor_x="center")
            else:
                arcade.draw_text(f"{self.name_2}: Выберите направление (↑)", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 145,
                                 arcade.color.YELLOW, 18, bold=True, anchor_x="center")
                arcade.draw_text(f"{self.name_1}: Выберите силу (W)", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 175,
                                 arcade.color.LIGHT_GRAY, 16, anchor_x="center")

        if self.game_state == "POWER":
            bar_width = 250
            bar_height = 25
            bar_x = SCREEN_WIDTH // 2 - bar_width // 2
            bar_y = 80

            arcade.draw_rect_filled(arcade.rect.XYWH(SCREEN_WIDTH // 2, bar_y, bar_width, bar_height),
                                    arcade.color.DARK_GRAY)

            fill_width = bar_width * (self.power / 100)
            arcade.draw_rect_filled(arcade.rect.XYWH(bar_x + fill_width // 2, bar_y,
                                                     fill_width, bar_height - 4),
                                    arcade.color.GREEN)

            arcade.draw_text(f"Сила: {int(self.power)}%", SCREEN_WIDTH // 2, bar_y + 35,
                             arcade.color.WHITE, 18, bold=True, anchor_x="center")

        if self.game_state == "GAME_OVER":
            arcade.draw_text("ИГРА ОКОНЧЕНА!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70,
                             arcade.color.RED, 32, bold=True, anchor_x="center")
            arcade.draw_text(f"Итоговый счет: {self.score} 🪙", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2, arcade.color.GOLD, 24, anchor_x="center")
            arcade.draw_text("Нажмите ESC для выхода", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2 - 70, arcade.color.LIGHT_GRAY, 18, anchor_x="center")

    def on_update(self, delta_time):
        if self.game_state == "GAME_OVER" or not self.game_started:
            return

        self.time_left -= delta_time
        if self.time_left <= 0:
            self.game_state = "GAME_OVER"
            arcade.play_sound(arcade.load_sound(":resources:sounds/gameover3.wav"), volume=0.6)
            return

        if self.ball:
            if not self.ball.in_pocket:
                # Проверка столкновения со стеной
                current_velocity = math.sqrt(self.ball.velocity_x ** 2 + self.ball.velocity_y ** 2)
                self.ball.update()

            if not self.ball.in_pocket and self.pocket:
                distance = math.sqrt(
                    (self.ball.center_x - self.pocket.center_x) ** 2 +
                    (self.ball.center_y - self.pocket.center_y) ** 2
                )

                if distance < 30:
                    self.ball.in_pocket = True
                    self.score += 10

                    # Воспроизведение звука попадания в лузку
                    arcade.play_sound(arcade.load_sound(":resources:sounds/coin3.wav"), volume=0.7)

                    self.create_random_positions()

                    self.aim_angle = 0
                    self.power = 0
                    self.game_state = "AIMING"

        if self.game_state == "SHOOTING" and self.ball and self.ball.is_stopped():
            self.aim_angle = 0
            self.power = 0
            self.game_state = "AIMING"

        if self.game_state == "AIMING":
            self.aim_angle += 1 * self.aim_direction

            if self.aim_angle > 360:
                self.aim_angle -= 360
            elif self.aim_angle < 0:
                self.aim_angle += 360

        elif self.game_state == "POWER":
            self.power += 1.5 * self.power_direction

            if self.power >= 100:
                self.power_direction = -1
                self.power = 100
                # Воспроизведение звука при достижении максимума силы
                arcade.play_sound(arcade.load_sound(":resources:sounds/jump3.wav"), volume=0.4)
            elif self.power <= 0:
                self.power_direction = 1
                self.power = 0

    def on_key_press(self, key, modifiers):
        if self.game_state == "GAME_OVER":
            return

        if key == arcade.key.R and self.game_state == "AIMING":
            self.player_turn = 2 if self.player_turn == 1 else 1
            self.aim_angle = 0
            self.power = 0
            # Воспроизведение звука смены игрока
            arcade.play_sound(arcade.load_sound(":resources:sounds/switch2.wav"), volume=0.3)
            return

        if self.game_state == "AIMING":
            if (self.player_turn == 1 and key == arcade.key.W) or \
                    (self.player_turn == 2 and key == arcade.key.UP):
                self.selected_angle = self.aim_angle
                self.game_state = "POWER"
                self.key_w_pressed = (key == arcade.key.W)
                self.key_up_pressed = (key == arcade.key.UP)

        elif self.game_state == "POWER":
            if (self.player_turn == 1 and key == arcade.key.UP) or \
                    (self.player_turn == 2 and key == arcade.key.W):
                if self.ball:
                    angle_rad = math.radians(self.selected_angle)
                    force = self.power * 0.5

                    self.ball.velocity_x = math.cos(angle_rad) * force
                    self.ball.velocity_y = math.sin(angle_rad) * force

                    self.game_state = "SHOOTING"

    def on_key_release(self, key, modifiers):
        if key == arcade.key.SPACE:
            if not self.game_started:
                self.game_started = True
                # Воспроизведение звука начала игры
                arcade.play_sound(arcade.load_sound(":resources:sounds/upgrade4.wav"), volume=0.4)

        if key == arcade.key.ESCAPE:
            from Game_windows import ChooseGame
            if self.game_state == "GAME_OVER":
                self.cursor.execute(f"""UPDATE data_players SET value = value + {self.score} WHERE id = 0""")
                self.conn.commit()
            self.window.show_view(ChooseGame())

        if key == arcade.key.W:
            self.key_w_pressed = False
        elif key == arcade.key.UP:
            self.key_up_pressed = False


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT)
    game_view = GolfGame()
    window.show_view(game_view)
    arcade.run()


if __name__ == "__main__":
    main()