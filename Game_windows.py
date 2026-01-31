import sys
import os
import arcade
import sqlite3


class StartView(arcade.View):
    def __init__(self):
        super().__init__()

        from arcade.gui import UIManager
        self.manager = UIManager(self.window)
        self.manager.enable()

        # Подключение к БД
        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        #Переменные игроков
        self.player1_name = self.load_player_name(1)
        self.player2_name = self.load_player_name(2)
        self.player1_bank = self.load_player_bank(1)
        self.player2_bank = self.load_player_bank(2)
        self.global_bank = 0

    def on_show_view(self):
        self.setup_ui()
        self.manager.enable()
        arcade.set_background_color(arcade.color.DARK_GREEN)

    def setup_ui(self):
        from arcade.gui import (
            UIFlatButton,
            UILabel,
            UIInputText,
            UIBoxLayout,
            UIAnchorLayout
        )

        root = UIAnchorLayout()
        v_box = UIBoxLayout(space_between=25, size_hint=(0.85, 0.9))
        bank_shop_container = UIBoxLayout(space_between=10, align="center", size_hint=(1.0, 0.1))

        # Общий банк
        global_bank_label = UILabel(text=f"🏆 ОБЩИЙ БАНК: {self.global_bank}",
        font_size=24, text_color=arcade.color.GOLD, bold=True, font_name="Arial")
        bank_shop_container.add(global_bank_label)

        # Магазин
        shop_button = UIFlatButton(text="🛒 МАГАЗИН", width=150,
        height=40, font_size=16, font_name="Arial")
        shop_button.on_click = self.on_shop_click
        bank_shop_container.add(shop_button)
        v_box.add(bank_shop_container)

        players_container = UIBoxLayout(vertical=False, space_between=20, size_hint=(1.0, 0.6))

        # ========ИГРОК 1========
        player1_container = UIAnchorLayout(width=400, height=300)
        player1_vbox = UIBoxLayout(space_between=15, align="center", size_hint=(0.8, 1.0))
        player1_anchor = UIAnchorLayout()
        player1_anchor.add(child=player1_vbox, anchor_x="left", anchor_y="center")

        # Заголовок игрока 1
        player1_title = UILabel(text="🎮 ИГРОК 1", font_size=20,
        text_color=arcade.color.CYAN, bold=True, font_name="Arial")
        player1_vbox.add(player1_title)

        # Поле ввода игрока 1
        self.player1_input = UIInputText(text=self.player1_name, width=200,
        height=35, font_size=18, font_name="Arial", multiline=False)
        self.player1_input.on_change = lambda event: self.change_player_name(event, player_id=1)
        player1_vbox.add(self.player1_input)

        # Банк игрока 1
        self.player1_bank_label = UILabel(text=f"💰 БАНК: {self.player1_bank}",
        font_size=22, text_color=arcade.color.GOLD, bold=True, font_name="Arial")
        player1_vbox.add(self.player1_bank_label)

        # Кнопка "Магазин" для игрока 1
        shop_btn_1 = UIFlatButton(text="🛒 ЛИЧНЫЙ МАГАЗИН", width=180,
        height=45, font_size=14, font_name="Arial")
        shop_btn_1.on_click = self.on_player1_shop_click
        player1_vbox.add(shop_btn_1)
        player1_container.add(player1_anchor)
        players_container.add(player1_container)

        # ========ИГРОК 2========
        player2_container = UIAnchorLayout(width=400, height=300)
        player2_vbox = UIBoxLayout(space_between=15, align="center", size_hint=(0.8, 1.0))
        player2_anchor = UIAnchorLayout()
        player2_anchor.add(child=player2_vbox, anchor_x="right", anchor_y="center")

        # Заголовок игрока 2
        player2_title = UILabel(text="🎮 ИГРОК 2", font_size=20,
        text_color=arcade.color.ORANGE_RED, bold=True, font_name="Arial")
        player2_vbox.add(player2_title)

        # Поле ввода игрока 2
        self.player2_input = UIInputText(text=self.player2_name, width=200,
        height=35, font_size=18, font_name="Arial", multiline=False)
        self.player2_input.on_change = lambda event: self.change_player_name(event, player_id=2)
        player2_vbox.add(self.player2_input)

        # Банк игрока 2
        self.player2_bank_label = UILabel(text=f"💰 БАНК: {self.player2_bank}",
        font_size=22, text_color=arcade.color.GOLD, bold=True, font_name="Arial")
        player2_vbox.add(self.player2_bank_label)

        # Кнопка "Магазин" для игрока 2
        shop_btn_2 = UIFlatButton(text="🛒 ЛИЧНЫЙ МАГАЗИН", width=180,
        height=45, font_size=14, font_name="Arial")
        shop_btn_2.on_click = self.on_player2_shop_click
        player2_vbox.add(shop_btn_2)
        player2_container.add(player2_anchor)
        players_container.add(player2_container)
        v_box.add(players_container)

        # Центральная кнопка "Играть"
        play_button_container = UIAnchorLayout()
        play_button = UIFlatButton(text="▶️ ИГРАТЬ", width=250,
        height=70, font_size=22, font_name="Arial", bold=True)
        play_button.on_click = self.on_play_click
        play_button_container.add(child=play_button, anchor_x="center", anchor_y="center")
        v_box.add(play_button_container)

        root.add(child=v_box, anchor_x="center", anchor_y="center")
        self.manager.add(root)

    # Обработчики событий
    def load_player_bank(self, player_id):
        table_name = f"data_player{player_id}"
        self.cursor.execute(f"SELECT bank FROM {table_name} WHERE id = ?",(player_id,))
        result = self.cursor.fetchone()
        return result[0]

    def load_player_name(self, player_id):
        table_name = f"data_player{player_id}"
        self.cursor.execute(f"SELECT name FROM {table_name} WHERE id = ?", (player_id,))
        result = self.cursor.fetchone()
        return result[0]

    def change_player_name(self, event, player_id):
        new_name = event.new_value
        table_name = f"data_player{player_id}"
        self.cursor.execute(f"UPDATE {table_name} SET name = ? WHERE id = ?",(new_name, player_id))
        self.conn.commit()


    def on_player1_shop_click(self, event):
        pass

    def on_player2_shop_click(self, event):
        pass

    def on_shop_click(self, event):
        pass

    def on_play_click(self, event):
        choose_game_view = ChooseGame()
        self.window.show_view(choose_game_view)

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_close(self):
        if self.conn:
            self.conn.close()


class ChooseGame(arcade.View):
    def __init__(self):
        super().__init__()

        from arcade.gui import UIManager
        self.manager = UIManager(self.window)

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(arcade.color.DARK_GREEN)
        self.setup_ui()

    def setup_ui(self):
        from arcade.gui import (
            UIFlatButton,
            UILabel,
            UIBoxLayout,
            UIAnchorLayout,
            UISpace
        )

        root = UIAnchorLayout()

        # Главный контейнер
        main_container = UIBoxLayout(space_between=30, size_hint=(0.95, 0.9))

        # Заголовок выбора игры
        title_label = UILabel(text="🎯 ВЫБЕРИТЕ РЕЖИМ ИГРЫ", font_size=32,
        font_name="Arial", text_color=arcade.color.GOLD, bold=True, align="center")
        main_container.add(title_label)
        modes_container = UIBoxLayout(vertical=False, space_between=40, size_hint=(1.0, 0.7))
        left_container = UIBoxLayout(space_between=15, size_hint=(0.45, 1.0))

        # Заголовок командного режима
        team_title = UILabel(text="🤝 КОМАНДНЫЙ РЕЖИМ", font_size=26,
        font_name="Arial", text_color=arcade.color.SKY_BLUE, bold=True, align="center")
        left_container.add(team_title)
        team_description_lines = ["🎮 Играйте вместе с другом",
            "💸 Деньги идут в общий банк", "🏆 Общие достижения"]
        for line in team_description_lines:
            line_label = UILabel(text=line, font_size=14, font_name="Arial",
            text_color=arcade.color.LIGHT_GRAY, align="center")
            left_container.add(line_label)
        left_container.add(UISpace(height=10))

        # Кнопки игр для командного режима
        games_team = ["🎲 ИГРА 1", "🎯 ИГРА 2", "🎪 ИГРА 3", "🎳 ИГРА 4", "🎨 ИГРА 5"]
        for i, game_text in enumerate(games_team, 1):
            game_btn = UIFlatButton(text=game_text, width=220,
            height=45, font_size=16, font_name="Arial")
            game_btn.on_click = getattr(self, f"on_team_game{i}_click")
            left_container.add(game_btn)
        modes_container.add(left_container)
        right_container = UIBoxLayout(space_between=15, size_hint=(0.45, 1.0))
        vs_title = UILabel(text="⚔️ РЕЖИМ ПРОТИВНИКА",
        font_size=26, font_name="Arial", text_color=arcade.color.ORANGE_RED,
        bold=True, align="center")
        right_container.add(vs_title)
        vs_description_lines = ["🎮 Соревнуйтесь друг с другом",
            "💸 Деньги идут в личный банк", "🏆 Побеждает сильнейший"]
        for line in vs_description_lines:
            line_label = UILabel(text=line, font_size=14, font_name="Arial",
            text_color=arcade.color.LIGHT_GRAY, align="center")
            right_container.add(line_label)
        right_container.add(UISpace(height=10))

        # Кнопки игр для режима друг против друга
        games_vs = ["🎾 Теннис", "🪳 Набег вредителей", "🕰️ Точный таймер", "🎳 ИГРА 4", "🎨 ИГРА 5"]
        for i, game_text in enumerate(games_vs, 1):
            game_btn = UIFlatButton(text=game_text, width=220, height=45,
            font_size=16, font_name="Arial")
            game_btn.on_click = getattr(self, f"on_vs_game{i}_click")
            right_container.add(game_btn)
        modes_container.add(right_container)
        main_container.add(modes_container)
        back_button_container = UIAnchorLayout(size_hint=(1.0, 0.15))

        # Кнопка "Назад"
        back_button = UIFlatButton(text="🔙 НАЗАД", width=200,
        height=50, font_size=18, font_name="Arial", bold=True)
        back_button.on_click = self.on_back_click
        back_button_container.add(child=back_button, anchor_x="center", anchor_y="center")
        main_container.add(back_button_container)

        root.add(child=main_container, anchor_x="center", anchor_y="center")
        self.manager.add(root)

    # Обработчики для командного режима
    def on_team_game1_click(self, event):
        print("Выбрана командная игра 1")
        # Здесь будет переход к выбранной игре

    def on_team_game2_click(self, event):
        print("Выбрана командная игра 2")
        # Здесь будет переход к выбранной игре

    def on_team_game3_click(self, event):
        print("Выбрана командная игра 3")
        # Здесь будет переход к выбранной игре

    def on_team_game4_click(self, event):
        print("Выбрана командная игра 4")
        # Здесь будет переход к выбранной игре

    def on_team_game5_click(self, event):
        print("Выбрана командная игра 5")
        # Здесь будет переход к выбранной игре

    # Обработчики для режима друг против друга
    def on_vs_game1_click(self, event):
        from Tennis import TennisGame
        self.window.show_view(TennisGame())

    def on_vs_game2_click(self, event):
        from Shooting import ShootingGame
        self.window.show_view(ShootingGame())

    def on_vs_game3_click(self, event):
        from Timer import TimerGame
        self.window.show_view(TimerGame())

    def on_vs_game4_click(self, event):
        print("Выбрана игра 4 (режим против друга)")
        # Здесь будет переход к выбранной игре

    def on_vs_game5_click(self, event):
        print("Выбрана игра 5 (режим против друга)")
        # Здесь будет переход к выбранной игре

    def on_back_click(self, event):
        # Возврат к стартовому окну
        start_view = StartView()
        self.window.show_view(start_view)

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()


def main():
    window = arcade.Window(900, 650, "Игра: Стартовое окно", resizable=False)
    start_view = StartView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()