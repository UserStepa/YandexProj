import arcade
import sqlite3
from arcade.gui import (
    UIManager,
    UIFlatButton,
    UILabel,
    UIInputText,
    UIBoxLayout,
    UIAnchorLayout,
)


class StartView(arcade.View):
    def __init__(self):
        super().__init__()

        self.manager = UIManager()
        self.manager.enable()

        # Подключение к БД
        self.conn = sqlite3.connect("2players_db.sqlite")
        self.cursor = self.conn.cursor()

        self.player1_name = self.load_player_name(1)
        self.player2_name = self.load_player_name(2)
        self.player1_bank = 0
        self.player2_bank = 0
        self.global_bank = 0

        self.setup_ui()

    def setup_ui(self):
        root = UIAnchorLayout()
        v_box = UIBoxLayout(space_between=25, size_hint=(0.85, 0.9))
        bank_shop_container = UIBoxLayout(space_between=10, align="center", size_hint=(1.0, 0.1))

        # Общий банк
        global_bank_label = UILabel(
            text=f"Общий банк: {self.global_bank}",
            font_size=20,
            text_color=arcade.color.GOLD,
            bold=True
        )
        bank_shop_container.add(global_bank_label)

        # Магазин
        shop_button = UIFlatButton(
            text="Магазин",
            width=120,
            height=35,
            font_size=14
        )
        shop_button.on_click = self.on_shop_click
        bank_shop_container.add(shop_button)
        v_box.add(bank_shop_container)

        players_container = UIBoxLayout(vertical=False, space_between=20, size_hint=(1.0, 0.6))

        # ========ИГРОК 1========
        player1_container = UIAnchorLayout(width=400, height=300)
        player1_vbox = UIBoxLayout(space_between=15, align="center", size_hint=(0.8, 1.0))
        player1_anchor = UIAnchorLayout()
        player1_anchor.add(child=player1_vbox, anchor_x="left", anchor_y="center")

        # Поле ввода игрока 1
        self.player1_input = UIInputText(
            text=self.player1_name,
            width=200,
            height=30,
            font_size=16,
            multiline=False
        )
        self.player1_input.on_change = self.on_player1_name_change
        player1_vbox.add(self.player1_input)

        # Банк игрока 1
        self.player1_bank_label = UILabel(
            text=f"Банк: {self.player1_bank}",
            font_size=20,
            text_color=arcade.color.GOLD
        )
        player1_vbox.add(self.player1_bank_label)

        # Контейнер для изображения скина игрока 1
        self.skin_image_container_1 = UIBoxLayout(width=170, height=80)
        player1_vbox.add(self.skin_image_container_1)

        # Кнопка "Выбрать скин" для игрока 1
        skin_btn_1 = UIFlatButton(text="Выбрать скин", width=150, height=45)
        skin_btn_1.on_click = self.on_player1_skin_click
        player1_vbox.add(skin_btn_1)

        player1_container.add(player1_anchor)
        players_container.add(player1_container)

        # ========ИГРОК 2========
        player2_container = UIAnchorLayout(width=400, height=300)
        player2_vbox = UIBoxLayout(space_between=15, align="center", size_hint=(0.8, 1.0))
        player2_anchor = UIAnchorLayout()
        player2_anchor.add(child=player2_vbox, anchor_x="right", anchor_y="center")

        # Поле ввода игрока 2
        self.player2_input = UIInputText(
            text=self.player2_name,
            width=200,
            height=30,
            font_size=16,
            multiline=False
        )
        self.player2_input.on_change = self.on_player2_name_change
        player2_vbox.add(self.player2_input)

        # Банк игрока 2
        self.player2_bank_label = UILabel(
            text=f"Банк: {self.player2_bank}",
            font_size=20,
            text_color=arcade.color.GOLD
        )
        player2_vbox.add(self.player2_bank_label)

        # Контейнер для изображения скина игрока 2
        self.skin_image_container_2 = UIBoxLayout(width=170, height=80)
        player2_vbox.add(self.skin_image_container_2)

        # Кнопка "Выбрать скин" для игрока 2
        skin_btn_2 = UIFlatButton(text="Выбрать скин", width=150, height=45)
        skin_btn_2.on_click = self.on_player2_skin_click
        player2_vbox.add(skin_btn_2)

        player2_container.add(player2_anchor)
        players_container.add(player2_container)

        v_box.add(players_container)

        # 3. Центральная кнопка "Играть"
        play_button_container = UIAnchorLayout()
        play_button = UIFlatButton(text="Играть", width=200, height=60, font_size=18, bold=True)
        play_button.on_click = self.on_play_click
        play_button_container.add(child=play_button, anchor_x="center", anchor_y="center")

        v_box.add(play_button_container)

        root.add(child=v_box, anchor_x="center", anchor_y="center")
        self.manager.add(root)

    # Обработчики событий
    def load_player_name(self, player_id):
        table_name = f"data_player{player_id}"
        self.cursor.execute(f"SELECT name FROM {table_name} WHERE id = ?", (player_id,))
        result = self.cursor.fetchone()
        return result[0]

    def save_player_name(self, player_id, new_name):
        table_name = f"data_player{player_id}"
        self.cursor.execute(f"UPDATE {table_name} SET name = ? WHERE id = ?",
                            (new_name, player_id))
        self.conn.commit()

    def on_player1_name_change(self, event):
        self.player1_name = event.new_value
        self.save_player_name(1, self.player1_name)

    def on_player2_name_change(self, event):
        self.player2_name = event.new_value
        self.save_player_name(2, self.player2_name)

    def on_player1_skin_click(self, event):
        pass

    def on_player2_skin_click(self, event):
        pass

    def on_shop_click(self, event):
        pass

    def on_play_click(self, event):
        pass

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(arcade.color.DARK_GREEN)

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_close(self):
        if self.conn:
            self.conn.close()


def main():
    window = arcade.Window(900, 650, "Игра: Стартовое окно", resizable=False)
    start_view = StartView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()