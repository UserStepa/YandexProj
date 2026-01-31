import arcade
import random
import time
import sqlite3

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Таймер-дуэль"


class TimerGame(arcade.View):
    def __init__(self):
        super().__init__()
        # Состояния игры
        self.game_state = "INSTRUCTION"  # INSTRUCTION, COUNTDOWN, TIMER_RUNNING, RESULTS

        # Настройки таймера
        self.target_time = 0
        self.current_time = 0
        self.start_time = 0

        # Результаты игроков
        self.player1_time = None
        self.player2_time = None
        self.player1_stopped = False
        self.player2_stopped = False

        # Таймер обратного отсчета
        self.countdown_time = 3
        self.countdown_start = 0

        # Цвета
        self.background_color = arcade.color.DARK_SLATE_GRAY
        self.player1_color = arcade.color.BLUE
        self.player2_color = arcade.color.RED
        self.text_color = arcade.color.WHITE
        self.highlight_color = arcade.color.GOLD

        # Настройка текста
        self.instruction_text = [
            "Выбейте более точное значение чем соперник!",
            "",
            "Нажмите: Space - чтобы начать, Esc - чтобы выйти.",
            "",
            "Стоп: W (левый игрок), Стрелка вверх (правый игрок)"]

        self.result_text = ""

        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        self.winner = None
        self.winner_id = 0

        self.setup()

    def setup(self):
        self.game_state = "INSTRUCTION"
        self.player1_time = None
        self.player2_time = None
        self.player1_stopped = False
        self.player2_stopped = False

    def start_game(self):
        self.game_state = "COUNTDOWN"
        self.target_time = random.randint(5, 15)
        self.countdown_start = time.time()

    def start_timer(self):
        self.game_state = "TIMER_RUNNING"
        self.start_time = time.time()
        self.current_time = 0

    def on_draw(self):
        self.clear()

        if self.game_state == "INSTRUCTION":
            self.draw_instructions()
        elif self.game_state == "COUNTDOWN":
            self.draw_countdown()
        elif self.game_state == "TIMER_RUNNING":
            self.draw_timer_running()
        elif self.game_state == "RESULTS":
            self.draw_results()

    def draw_instructions(self):
        # Заголовок
        arcade.draw_text("ТОЧНЫЙ ТАЙМЕР",
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT - 100,
                         arcade.color.GOLD,
                         36,
                         anchor_x="center",
                         bold=True)

        # Инструкция
        for i, line in enumerate(self.instruction_text):
            arcade.draw_text(line,
                             SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT - 200 - i * 40,
                             self.text_color,
                             24,
                             anchor_x="center")

        arcade.draw_text("Нажмите SPACE для начала игры",
                         SCREEN_WIDTH // 2,
                         100,
                         arcade.color.LIME_GREEN,
                         28,
                         anchor_x="center",
                         bold=True)

    def draw_countdown(self):
        elapsed = time.time() - self.countdown_start
        countdown_value = self.countdown_time - int(elapsed)

        if countdown_value > 0:
            # Отображение обратного отсчета
            arcade.draw_text(str(countdown_value),
                             SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2,
                             self.highlight_color,
                             120,
                             anchor_x="center",
                             bold=True)

            # Цель
            arcade.draw_text(f"Остановите на {self.target_time} сек.",
                             SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2 - 150,
                             self.text_color,
                             36,
                             anchor_x="center")
        else:
            self.start_timer()

    def draw_timer_running(self):
        self.current_time = time.time() - self.start_time

        # Основной таймер
        arcade.draw_text(f"{self.current_time:.2f}",
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT // 2 + 50,
                         self.highlight_color,
                         96,
                         anchor_x="center",
                         bold=True)

        # Целевое время
        arcade.draw_text(f"Цель: {self.target_time} сек.",
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT // 2 - 50,
                         self.text_color,
                         36,
                         anchor_x="center")

        # Поле левого игрока
        arcade.draw_rect_filled(arcade.rect.XYWH(SCREEN_WIDTH // 4,
                                     SCREEN_HEIGHT // 4,
                                     200, 100),
                                     self.player1_color)

        # Результат левого игрока
        if self.player1_stopped:
            result_text = f"{self.player1_time:.2f}"
            color = arcade.color.GOLD
        else:
            result_text = "Ждем..."
            color = arcade.color.WHITE

        arcade.draw_text(result_text,
                         SCREEN_WIDTH // 4,
                         SCREEN_HEIGHT // 4,
                         color,
                         32,
                         anchor_x="center")

        arcade.draw_text("W",
                         SCREEN_WIDTH // 4,
                         SCREEN_HEIGHT // 4 - 60,
                         arcade.color.WHITE,
                         20,
                         anchor_x="center")

        # Поле правого игрока
        arcade.draw_rect_filled(arcade.rect.XYWH(SCREEN_WIDTH * 3 // 4,
                                     SCREEN_HEIGHT // 4,
                                     200, 100),
                                     self.player2_color)

        # Результат правого игрока
        if self.player2_stopped:
            result_text = f"{self.player2_time:.2f}"
            color = arcade.color.GOLD
        else:
            result_text = "Ждем..."
            color = arcade.color.WHITE

        arcade.draw_text(result_text,
                         SCREEN_WIDTH * 3 // 4,
                         SCREEN_HEIGHT // 4,
                         color,
                         32,
                         anchor_x="center")

        arcade.draw_text("↑",
                         SCREEN_WIDTH * 3 // 4,
                         SCREEN_HEIGHT // 4 - 60,
                         arcade.color.WHITE,
                         20,
                         anchor_x="center")

        arcade.draw_text("Нажмите свою кнопку, когда думаете, что прошло целевое время",
                         SCREEN_WIDTH // 2,
                         40,
                         arcade.color.LIME_GREEN,
                         20,
                         anchor_x="center")

    def draw_results(self):
        self.cursor.execute("SELECT name FROM data_player1 WHERE id = 1", )
        result = self.cursor.fetchone()
        self.name_1 = result[0]

        self.cursor.execute("SELECT name FROM data_player2 WHERE id = 2", )
        result = self.cursor.fetchone()
        self.name_2 = result[0]

        # Заголовок
        arcade.draw_text("РЕЗУЛЬТАТЫ",
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT - 100,
                         arcade.color.GOLD,
                         48,
                         anchor_x="center",
                         bold=True)

        # Целевое время
        arcade.draw_text(f"Целевое время: {self.target_time} сек.",
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT - 180,
                         self.text_color,
                         32,
                         anchor_x="center")

        # Результат игрока 1
        diff1 = abs(self.target_time - self.player1_time)
        arcade.draw_text(f"{self.name_1}: {self.player1_time:.2f} сек. (отклонение: {diff1:.2f})",
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT // 2 + 50,
                         self.player1_color,
                         32,
                         anchor_x="center")

        # Результат игрока 2
        diff2 = abs(self.target_time - self.player2_time)
        arcade.draw_text(f"{self.name_2}: {self.player2_time:.2f} сек. (отклонение: {diff2:.2f})",
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT // 2,
                         self.player2_color,
                         32,
                         anchor_x="center")

        # Определение победителя
        if diff1 < diff2:
            self.winner_id = 1
            self.winner = self.name_1
            winner_text = f"ПОБЕДИТЕЛЬ: {self.winner}! (+10🪙)"
        elif diff2 < diff1:
            self.winner_id = 2
            self.winner = self.name_2
            winner_text = f"ПОБЕДИТЕЛЬ: {self.winner}! (+10🪙)"
        else:
            winner_text = "НИЧЬЯ!"
            winner_color = arcade.color.GOLD

        arcade.draw_text(winner_text,
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT // 2 - 100,
                         arcade.color.GOLD,
                         42,
                         anchor_x="center",
                         bold=True)

        # Инструкция для продолжения
        arcade.draw_text("Нажмите SPACE для новой игры или ESC для выхода",
                         SCREEN_WIDTH // 2,
                         100,
                         arcade.color.LIME_GREEN,
                         24,
                         anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            from Game_windows import ChooseGame
            if self.game_state == "RESULTS" and self.winner_id != 0:
                self.cursor.execute(f"""UPDATE data_player{self.winner_id} 
                            SET bank = bank + ? WHERE id = ?""", (10, self.winner_id))
                self.conn.commit()
            self.window.show_view(ChooseGame())


        elif self.game_state == "INSTRUCTION":
            if key == arcade.key.SPACE:
                self.start_game()

        elif self.game_state == "TIMER_RUNNING":
            if key == arcade.key.W and not self.player1_stopped:
                self.player1_time = self.current_time
                self.player1_stopped = True

            elif key == arcade.key.UP and not self.player2_stopped:
                self.player2_time = self.current_time
                self.player2_stopped = True

            if self.player1_stopped and self.player2_stopped:
                self.game_state = "RESULTS"

        elif self.game_state == "RESULTS":
            if key == arcade.key.SPACE:
                self.setup()
                self.start_game()

    def on_update(self, delta_time):
        if self.game_state == "TIMER_RUNNING":
            self.current_time = time.time() - self.start_time
        elif self.game_state == "COUNTDOWN":
            elapsed = time.time() - self.countdown_start
            if elapsed >= self.countdown_time:
                self.start_timer()