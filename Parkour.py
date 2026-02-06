import arcade
import random
import time
import sqlite3

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650
TILE_SCALING = 1
PLAYER_MOVEMENT_SPEED = 3
CAMERA_LERP = 0.05
GRAVITY = 0.8
PLAYER_JUMP_SPEED = 15
PLAYER_JUMP_SPEED_ALT = 12
LADDER_CLIMB_SPEED = 4  # Скорость подъема по лестнице
TOTAL_COINS = 15
GAME_TIME = 60


class ParkourGame(arcade.View):
    def __init__(self):
        super().__init__()
        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        self.world_camera = arcade.camera.Camera2D()
        self.ui_camera = arcade.camera.Camera2D()
        self.world_width = SCREEN_WIDTH
        self.world_height = SCREEN_HEIGHT

        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.boom_list = arcade.SpriteList()
        self.collision_list = arcade.SpriteList()
        self.ladder_list = arcade.SpriteList()
        self.lava_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()

        # Переменные состояния
        self.game_over = False
        self.game_started = False
        self.start_time = time.time()
        self.collected_coins = 0

        # Переменные управления
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        # Переменные прыжков
        self.jump_count = 0
        self.can_double_jump = True
        self.is_on_ground = False
        self.on_ladder = False

        self.physics_engine = None
        self.background_color = arcade.color.GRAY

        self.setup()

    def setup(self):
        self.cursor.execute("SELECT value FROM data_players WHERE id = 6")
        result = self.cursor.fetchone()
        if result[0] == 1:
            self.tile_map = arcade.load_tilemap("images/parkour/map_2.tmx", TILE_SCALING)
        else:
            self.tile_map = arcade.load_tilemap("images/parkour/map.tmx", TILE_SCALING)

        self.world_width = int(self.tile_map.width * self.tile_map.tile_width * TILE_SCALING)
        self.world_height = int(self.tile_map.height * self.tile_map.tile_height * TILE_SCALING)

        self.player_sprite = arcade.Sprite('images/parkour/player.png', 0.7)
        self.player_sprite.center_x = 450
        self.player_sprite.center_y = 45
        self.player_list.append(self.player_sprite)

        self.wall_list = self.tile_map.sprite_lists.get("walls", arcade.SpriteList())
        self.collision_list = self.tile_map.sprite_lists.get("collision", arcade.SpriteList())
        self.ladder_list = self.tile_map.sprite_lists.get("ladders", arcade.SpriteList())
        self.lava_list = self.tile_map.sprite_lists.get("lava", arcade.SpriteList())
        self.boom_list = self.tile_map.sprite_lists.get("boom", arcade.SpriteList())

        if len(self.collision_list) == 0:
            self.collision_list = self.wall_list

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            self.collision_list,
            gravity_constant=GRAVITY
        )

        self.create_coins()

    def create_coins(self):
        # Границы карты
        min_x = 50
        max_x = self.world_width - 50
        min_y = 50
        max_y = self.world_height - 50

        coins_created = 0

        while coins_created < TOTAL_COINS:
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)

            coin = arcade.Sprite('images/parkour/coin.png', 0.7)
            coin.center_x = x
            coin.center_y = y

            if not arcade.check_for_collision_with_list(coin, self.collision_list) and \
                    not arcade.check_for_collision_with_list(coin, self.lava_list) and \
                    not arcade.check_for_collision_with_list(coin, self.boom_list):

                if not arcade.check_for_collision_with_list(coin, self.coin_list):
                    self.coin_list.append(coin)
                    coins_created += 1

    def on_draw(self):
        self.clear()
        if self.game_over:
            self.ui_camera.use()
            arcade.draw_text("ИГРА ОКОНЧЕНА!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70,
                             arcade.color.RED, 32, bold=True, anchor_x="center")
            arcade.draw_text(f"Итоговый счет: {self.collected_coins} 🪙", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2, arcade.color.GOLD, 24, anchor_x="center")
            arcade.draw_text("Нажмите ESC для выхода", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2 - 70, arcade.color.LIGHT_GRAY, 18, anchor_x="center")
            return

        if not self.game_started and not self.game_over:
            arcade.draw_text("Собирайте монеты, оставайтесь в живых!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140,
                             arcade.color.BLACK, 32, bold=True, anchor_x="center")
            arcade.draw_text("игрок 1 - влево(A)-вправо(D), игрок 2 - вверх(↑)-вниз(↓)", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70,
                             arcade.color.BLACK, 24, bold=True, anchor_x="center")
            arcade.draw_text("Нажмите: Space - чтобы начать, Esc - чтобы выйти", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2, arcade.color.BLACK, 24, anchor_x="center")
            return

        self.world_camera.use()
        self.wall_list.draw()
        self.ladder_list.draw()
        self.lava_list.draw()
        self.boom_list.draw()
        self.coin_list.draw()
        self.player_list.draw()

        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, GAME_TIME - int(elapsed_time))

        self.ui_camera.use()

        # Таймер
        timer_color = arcade.color.GREEN if remaining_time > 10 else arcade.color.RED
        arcade.draw_text(f"Время: {remaining_time} сек",
                         20, SCREEN_HEIGHT - 20,
                         timer_color, 24, bold=True)

        # Счетчик монеток
        coins_color = arcade.color.GOLD
        arcade.draw_text(f"Монетки: {self.collected_coins}/{TOTAL_COINS}",
                         SCREEN_WIDTH - 250, SCREEN_HEIGHT - 20,
                         coins_color, 24, bold=True)

    def update_player_speed(self):
        if self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0

        # Движение по лестнице
        if self.on_ladder:
            if self.up_pressed and not self.down_pressed:
                self.player_sprite.change_y = LADDER_CLIMB_SPEED
            elif self.down_pressed and not self.up_pressed:
                self.player_sprite.change_y = -LADDER_CLIMB_SPEED
            else:
                self.player_sprite.change_y = 0

    def check_collisions(self):
        if self.game_over:
            return

        self.player_sprite.center_y -= 2
        on_ground = arcade.check_for_collision_with_list(self.player_sprite, self.collision_list)
        self.player_sprite.center_y += 2

        self.is_on_ground = len(on_ground) > 0
        if self.is_on_ground:
            self.jump_count = 0
            self.can_double_jump = True

        # Проверка на лестницу
        ladder_collision = arcade.check_for_collision_with_list(self.player_sprite, self.ladder_list)
        self.on_ladder = len(ladder_collision) > 0
        if self.on_ladder:
            current_y_speed = self.player_sprite.change_y
            self.player_sprite.change_y = 0
            if self.up_pressed:
                self.player_sprite.center_y += LADDER_CLIMB_SPEED
                if arcade.check_for_collision_with_list(self.player_sprite, self.collision_list):
                    self.player_sprite.center_y -= LADDER_CLIMB_SPEED
            elif self.down_pressed:
                self.player_sprite.center_y -= LADDER_CLIMB_SPEED
                if arcade.check_for_collision_with_list(self.player_sprite, self.collision_list):
                    self.player_sprite.center_y += LADDER_CLIMB_SPEED

            self.player_sprite.change_y = current_y_speed

        lava_collisions = arcade.check_for_collision_with_list(self.player_sprite, self.lava_list)
        boom_collisions = arcade.check_for_collision_with_list(self.player_sprite, self.boom_list)
        if boom_collisions or lava_collisions:
            self.game_over = True

        # Cбор монеток
        coin_collisions = arcade.check_for_collision_with_list(self.player_sprite, self.coin_list)
        for coin in coin_collisions:
            coin.remove_from_sprite_lists()
            self.collected_coins += 1

            if self.collected_coins >= TOTAL_COINS:
                self.game_over = True

    def on_update(self, delta_time):
        if self.game_over:
            return

        elapsed_time = time.time() - self.start_time
        if elapsed_time >= GAME_TIME:
            self.game_over = True
            return

        # Обновляем позицию камеры
        position = (
            self.player_sprite.center_x,
            self.player_sprite.center_y
        )
        self.world_camera.position = arcade.math.lerp_2d(
            self.world_camera.position,
            position,
            CAMERA_LERP,
        )

        self.update_player_speed()
        self.check_collisions()

        if self.game_over:
            return

        if not self.on_ladder:  # На лестнице гравитация отключена
            self.physics_engine.update()

            if self.player_sprite.change_x > 0:
                self.player_sprite.center_x += self.player_sprite.change_x
                if arcade.check_for_collision_with_list(self.player_sprite, self.collision_list):
                    self.player_sprite.center_x -= self.player_sprite.change_x
            elif self.player_sprite.change_x < 0:
                self.player_sprite.center_x += self.player_sprite.change_x
                if arcade.check_for_collision_with_list(self.player_sprite, self.collision_list):
                    self.player_sprite.center_x -= self.player_sprite.change_x

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            from Game_windows import ChooseGame
            if self.game_over:
                self.cursor.execute(f"""UPDATE data_players SET value = value + {self.collected_coins} WHERE id = 0""")
                self.conn.commit()
            self.window.show_view(ChooseGame())

        if key == arcade.key.SPACE:
            if not self.game_started:
                self.game_started = True

        if key == arcade.key.UP:
            if not self.on_ladder:
                self.handle_jump()
            else:
                self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.D:
            self.right_pressed = True

    def on_key_release(self, key, modifiers):
        if self.game_over:
            return

        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.D:
            self.right_pressed = False

    def handle_jump(self):
        if self.on_ladder:
            return

        if self.is_on_ground:
            self.player_sprite.change_y = PLAYER_JUMP_SPEED
            self.jump_count = 1
            self.is_on_ground = False
        elif self.can_double_jump and self.jump_count == 1:
            self.player_sprite.change_y = PLAYER_JUMP_SPEED_ALT
            self.jump_count = 2
            self.can_double_jump = False


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT)
    window.show_view(ParkourGame())
    arcade.run()


if __name__ == "__main__":
    main()