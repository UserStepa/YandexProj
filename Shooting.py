import arcade
import random
import sqlite3

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650


class Pest(arcade.Sprite):
    def __init__(self, texture, size, side, window_width, window_height, speed=2, vertical_zone=None):
        super().__init__(texture, scale=size)

        self.side = side
        self.window_width = window_width
        self.window_height = window_height
        self.speed = speed
        self.vertical_zone = vertical_zone

        # Начальная позиция
        self._generate_initial_position()

        # Начальное случайное направление
        self.change_x = random.uniform(-self.speed, self.speed)
        self.change_y = random.uniform(-self.speed, self.speed)

        # Границы для движения
        self._set_movement_bounds()

    def _calculate_horizontal_bounds(self, with_padding=True):
        padding = self.width / 2 if with_padding else 0

        if self.side == 1:
            min_x = 0 + padding
            max_x = self.window_width / 2 - padding
        else:
            min_x = self.window_width / 2 + padding
            max_x = self.window_width - padding

        return min_x, max_x

    def _calculate_vertical_bounds(self, with_padding=True):
        padding = self.height / 2 if with_padding else 0

        if self.vertical_zone == 'bottom':
            min_y = 0 + padding
            max_y = self.window_height * 0.33 - padding
        elif self.vertical_zone == 'middle':
            min_y = self.window_height * 0.33 + padding
            max_y = self.window_height * 0.67 - padding
        elif self.vertical_zone == 'top':
            min_y = self.window_height * 0.67 + padding
            max_y = self.window_height - padding
        else:
            min_y = 0 + padding
            max_y = self.window_height - padding

        return min_y, max_y

    def _generate_initial_position(self):
        min_x, max_x = self._calculate_horizontal_bounds(with_padding=False)
        min_y, max_y = self._calculate_vertical_bounds(with_padding=False)

        # Отступы для спрайта
        min_x += self.width / 2
        max_x -= self.width / 2
        min_y += self.height / 2
        max_y -= self.height / 2

        # Случайная позиция
        self.center_x = random.uniform(min_x, max_x)
        self.center_y = random.uniform(min_y, max_y)

    def _set_movement_bounds(self):
        self.min_x, self.max_x = self._calculate_horizontal_bounds(with_padding=True)
        self.min_y, self.max_y = self._calculate_vertical_bounds(with_padding=True)

    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Обработка границ по X
        if self.center_x <= self.min_x:
            self.center_x = self.min_x
            self.change_x = abs(self.change_x)
        elif self.center_x >= self.max_x:
            self.center_x = self.max_x
            self.change_x = -abs(self.change_x)

        # Обработка границ по Y
        if self.center_y <= self.min_y:
            self.center_y = self.min_y
            self.change_y = abs(self.change_y)
        elif self.center_y >= self.max_y:
            self.center_y = self.max_y
            self.change_y = -abs(self.change_y)

        # Случайное изменение направления
        if random.random() < 0.01:
            self.change_x = random.uniform(-self.speed, self.speed)
            self.change_y = random.uniform(-self.speed, self.speed)


class ShootingGame(arcade.View):
    def __init__(self):
        super().__init__()

        self.texture = arcade.load_texture("images/shooting/shooting_background.png")

        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        self.player1_texture = self.load_texture("data_player1", 1)
        self.player2_texture = self.load_texture("data_player2", 2)

        # Прицелы игроков
        self.crosshair_1 = arcade.Sprite("images/shooting/crosshair_blue.png",
                                         center_x=225, center_y=325, scale=1.2)
        self.crosshair_2 = arcade.Sprite("images/shooting/crosshair_red.png",
                                         center_x=675, center_y=325, scale=1.2)

        self.pest_batch = arcade.SpriteList()
        self.all_sprites_batch = arcade.SpriteList()

        # Отдельные списки для удобства доступа
        self.pests_left = []
        self.pests_right = []

        self.score_left = 0
        self.score_right = 0

        self.game_started = False
        self.game_over = False
        self.winner = None
        self.winner_id = 0

        self.keys_pressed = set()
        self.crosshair_speed = 5

        # Настройки попадания
        self.hit_tolerance_moving = 30

        # Текстуры вредителей
        self.texture_pests = []

        self.setup()

    def load_texture(self, name, id):
        self.cursor.execute(f"SELECT name FROM {name} WHERE value = 1")
        result = self.cursor.fetchone()
        texture = arcade.load_texture(f"images/data_player{id}/{result[0]}.png")
        return texture

    def setup(self):
        self.cursor.execute("SELECT value FROM data_players WHERE id = 7")
        result = self.cursor.fetchone()
        if result[0] == 1:
            self.texture_pests = [
                arcade.load_texture("images/shooting/rat_des.png"),
                arcade.load_texture("images/shooting/cockroach_des.png"),
                arcade.load_texture("images/shooting/fly_des.png")
            ]
        else:
            self.texture_pests = [
                arcade.load_texture("images/shooting/rat.png"),
                arcade.load_texture("images/shooting/cockroach.png"),
                arcade.load_texture("images/shooting/fly.png")
            ]

        self.score_left = 0
        self.score_right = 0
        self.game_over = False
        self.winner = None
        self.keys_pressed.clear()

        self.pests_right.clear()
        self.pests_left.clear()
        self.pest_batch.clear()
        self.all_sprites_batch.clear()

        # Крысы (нижняя часть экрана)
        for _ in range(2):
            texture = self.texture_pests[0]
            speed = random.uniform(2, 3)

            pest_left = Pest(texture=texture, size=0.15, side=1,
                             window_width=self.window.width, window_height=self.window.height,
                             speed=speed, vertical_zone='bottom')

            pest_right = Pest(texture=texture, size=0.15, side=2,
                              window_width=self.window.width, window_height=self.window.height,
                              speed=speed, vertical_zone='bottom')

            self.pests_left.append(pest_left)
            self.pests_right.append(pest_right)
            self.pest_batch.append(pest_left)
            self.pest_batch.append(pest_right)

        # Тараканы (средняя часть экрана)
        for _ in range(3):
            texture = self.texture_pests[1]
            speed = random.uniform(4, 6)

            pest_left = Pest(texture=texture, size=0.08, side=1,
                             window_width=self.window.width, window_height=self.window.height,
                             speed=speed, vertical_zone='middle')

            pest_right = Pest(texture=texture, size=0.08, side=2,
                              window_width=self.window.width, window_height=self.window.height,
                              speed=speed, vertical_zone='middle')

            self.pests_left.append(pest_left)
            self.pests_right.append(pest_right)
            self.pest_batch.append(pest_left)
            self.pest_batch.append(pest_right)

        # Мухи (верхняя часть экрана)
        for _ in range(5):
            texture = self.texture_pests[2]
            speed = random.uniform(6, 8)

            pest_left = Pest(texture=texture, size=0.05, side=1,
                             window_width=self.window.width, window_height=self.window.height,
                             speed=speed, vertical_zone='top')

            pest_right = Pest(texture=texture, size=0.05, side=2,
                              window_width=self.window.width, window_height=self.window.height,
                              speed=speed, vertical_zone='top')

            self.pests_left.append(pest_left)
            self.pests_right.append(pest_right)
            self.pest_batch.append(pest_left)
            self.pest_batch.append(pest_right)

        # Добавляем прицелы в общий batch
        self.all_sprites_batch.append(self.crosshair_1)
        self.all_sprites_batch.append(self.crosshair_2)

        self.crosshair_1.center_x = 225
        self.crosshair_1.center_y = 325
        self.crosshair_2.center_x = 675
        self.crosshair_2.center_y = 325

    def on_draw(self):
        self.clear()

        # Отрисовка фона
        arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(
            self.window.width // 2, self.window.height // 2,
            self.window.width, self.window.height))

        # Разделительная линия
        arcade.draw_line(self.window.width / 2, 0,
                         self.window.width / 2, self.window.height,
                         arcade.color.WHITE, 2)

        if not self.game_started and not self.game_over:
            arcade.draw_text("Убейте всех вредителей быстрее соперника!",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, arcade.color.BLACK, 30, anchor_x="center")
            arcade.draw_text("Нажмите: Space - чтобы начать, Esc - чтобы выйти",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.BLACK, 20, anchor_x="center")
            arcade.draw_text("Выстрел: E (левый игрок), . (правый игрок)",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50, arcade.color.BLACK, 20, anchor_x="center")
            return

        if self.game_over:
            arcade.draw_text(f"Игра закончена! Победил {self.winner} (+10🪙)",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100, arcade.color.GOLD, 30, anchor_x="center")
            arcade.draw_text(f"Нажмите Esc чтобы вернуться в меню",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, arcade.color.WHITE, 20, anchor_x="center")
            return

        self.pest_batch.draw()
        self.all_sprites_batch.draw()

        # Аватары игроков
        arcade.draw_texture_rect(self.player1_texture, arcade.rect.XYWH(
            SCREEN_WIDTH // 2 - 65, SCREEN_HEIGHT - 50, 70, 70))

        arcade.draw_texture_rect(self.player2_texture, arcade.rect.XYWH(
            SCREEN_WIDTH // 2 + 65, SCREEN_HEIGHT - 50, 70, 70))

        # Отображение счета
        arcade.draw_text(f"Счет: {self.score_left}",
                         SCREEN_WIDTH / 4, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 20, anchor_x="center")
        arcade.draw_text(f"Счет: {self.score_right}",
                         SCREEN_WIDTH * 3 / 4, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 20, anchor_x="center")

    def on_update(self, delta_time):
        if not self.game_started or self.game_over:
            return

        # Обновление всех вредителей
        for pest in self.pest_batch:
            pest.update()

        self._update_crosshair_movement()
        self._constrain_crosshairs()

        if self.score_left >= 10:
            self.game_over = True
            self.cursor.execute("SELECT name FROM data_player1 WHERE id = 0")
            result = self.cursor.fetchone()
            self.winner = result[0]
            self.winner_id = 1
        elif self.score_right >= 10:
            self.game_over = True
            self.cursor.execute("SELECT name FROM data_player2 WHERE id = 0")
            result = self.cursor.fetchone()
            self.winner = result[0]
            self.winner_id = 2

    def _update_crosshair_movement(self):
        # Движение левого прицела
        if arcade.key.W in self.keys_pressed:
            self.crosshair_1.center_y += self.crosshair_speed
        if arcade.key.S in self.keys_pressed:
            self.crosshair_1.center_y -= self.crosshair_speed
        if arcade.key.A in self.keys_pressed:
            self.crosshair_1.center_x -= self.crosshair_speed
        if arcade.key.D in self.keys_pressed:
            self.crosshair_1.center_x += self.crosshair_speed

        # Движение правого прицела
        if arcade.key.UP in self.keys_pressed:
            self.crosshair_2.center_y += self.crosshair_speed
        if arcade.key.DOWN in self.keys_pressed:
            self.crosshair_2.center_y -= self.crosshair_speed
        if arcade.key.LEFT in self.keys_pressed:
            self.crosshair_2.center_x -= self.crosshair_speed
        if arcade.key.RIGHT in self.keys_pressed:
            self.crosshair_2.center_x += self.crosshair_speed

    def _constrain_crosshairs(self):
        # Ограничение движения прицелов в пределах своей половины экрана
        self.crosshair_1.center_x = max(self.crosshair_1.width / 2,
                                        min(self.window.width / 2 - self.crosshair_1.width / 2,
                                            self.crosshair_1.center_x))
        self.crosshair_1.center_y = max(self.crosshair_1.height / 2,
                                        min(self.window.height - self.crosshair_1.height / 2,
                                            self.crosshair_1.center_y))

        self.crosshair_2.center_x = max(self.window.width / 2 + self.crosshair_2.width / 2,
                                        min(self.window.width - self.crosshair_2.width / 2,
                                            self.crosshair_2.center_x))
        self.crosshair_2.center_y = max(self.crosshair_2.height / 2,
                                        min(self.window.height - self.crosshair_2.height / 2,
                                            self.crosshair_2.center_y))

    def _check_hit(self, crosshair, target, is_stationary=False):
        distance = ((crosshair.center_x - target.center_x) ** 2 +
                    (crosshair.center_y - target.center_y) ** 2) ** 0.5

        return distance < self.hit_tolerance_moving

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            if not self.game_started:
                self.game_started = True

        if key == arcade.key.ESCAPE:
            from Game_windows import ChooseGame
            if self.game_over:
                self.cursor.execute(f"""UPDATE data_player{self.winner_id} 
                SET value = value + 10 WHERE id = 0""")
                self.conn.commit()
            self.window.show_view(ChooseGame())

        if key in [arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D,
                   arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT]:
            self.keys_pressed.add(key)

        # Стрельба левого игрока (E)
        elif key == arcade.key.E:
            hit_any = False
            for pest in list(self.pests_left):
                if pest in self.pest_batch and self._check_hit(self.crosshair_1, pest):
                    self.pest_batch.remove(pest)
                    self.pests_left.remove(pest)
                    self.score_left += 1
                    hit_any = True

        # Стрельба правого игрока (.)
        elif key == arcade.key.PERIOD:
            hit_any = False
            for pest in list(self.pests_right):
                if pest in self.pest_batch and self._check_hit(self.crosshair_2, pest):
                    self.pest_batch.remove(pest)
                    self.pests_right.remove(pest)
                    self.score_right += 1
                    hit_any = True

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D,
                   arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT]:
            self.keys_pressed.discard(key)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT)
    game_view = ShootingGame()
    window.show_view(game_view)
    arcade.run()


if __name__ == "__main__":
    main()