
import os
import math
import random
import heapq

from kivy.app import App
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.audio import SoundLoader
from kivy.core.text import Label as CoreLabel
from kivy.graphics import (
    Color, Rectangle, RoundedRectangle, Ellipse, Line
)
from kivy.uix.widget import Widget
from kivy.core.window import Window


# ==================================================
# CONFIGURATION
# ==================================================

VIRTUAL_W = 1920
VIRTUAL_H = 1080

TILE = 90
FPS = 60

Window.fullscreen = "auto"


# ==================================================
# ASSETS
# ==================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def asset_path(filename):
    return os.path.join(BASE_DIR, "assets", filename)

def audio_path(filename):
    return os.path.join(BASE_DIR, "audio", filename)


def load_texture(filename):
    path = asset_path(filename)
    if not os.path.isfile(path):
        print("Missing image:", path)
        return None

    try:
        return CoreImage(path).texture
    except Exception as error:
        print("Image error:", filename, error)
        return None


def load_sound(filename):
    path = audio_path(filename)
    if not os.path.isfile(path):
        print("Missing audio:", path)
        return None

    try:
        return SoundLoader.load(path)
    except Exception as error:
        print("Audio error:", filename, error)
        return None


# ==================================================
# IMAGES
# ==================================================

player_texture = load_texture("behrad.jpg")

enemy_textures = {
    "PEZHMAN": load_texture("pezhman.jpg"),
    "HOSSEINI": load_texture("hosseini.jpg"),
    "AASEF": load_texture("aasef.jpg"),
    "MIRZAEE": load_texture("mirzaaee.jpg"),
    "ZAADPOUR": load_texture("zaadpoor.jpg")
}

logo_texture = load_texture("shahrfarsh.png")

portrait_textures = [
    load_texture("pezhman.jpg"),
    load_texture("zaadpoor.jpg"),
    load_texture("mirzaaee.jpg")
]

sounds = {
    "DEFAULT": load_sound("horror_music.mp3"),
    "HOSSEINI": load_sound("hosseini.mp3")
}


# ==================================================
# CHARACTERS
# ==================================================

enemies = {
    "PEZHMAN": {
        "speed": 90,
        "dialogue": "Delet Jamali mikhad ya man?"
    },
    "HOSSEINI": {
        "speed": 110,
        "dialogue": "hazrateee yaaarrrrrr"
    },
    "AASEF": {
        "speed": 110,
        "dialogue": "khodai shabih amlaki ha nistam"
    },
    "MIRZAEE": {
        "speed": 150,
        "dialogue": "Mordeshooreto bebaran!"
    },
    "ZAADPOUR": {
        "speed": 210,
        "dialogue": "Tasavoresh kon!"
    }
}

WHITE = (240, 240, 220)
YELLOW = (190, 170, 95)
RED = (210, 35, 35)


# ==================================================
# MAP
# ==================================================

world = [
    "111111111111111111",
    "100000000000000001",
    "101111011111011101",
    "100001000001000001",
    "111101111101111101",
    "100000000000000001",
    "101111011111011101",
    "100001000001000001",
    "111101111101111101",
    "100000000000000001",
    "101111011111011101",
    "100000000000000001",
    "111111111111111111"
]

ROWS = len(world)
COLS = len(world[0])

MAP_WIDTH = COLS * TILE
MAP_HEIGHT = ROWS * TILE


def is_open(col, row):
    return (
        0 <= col < COLS
        and 0 <= row < ROWS
        and world[row][col] == "0"
    )


def world_to_tile(x, y):
    return int(x // TILE), int(y // TILE)


def tile_center(tile):
    col, row = tile
    return (
        col * TILE + TILE // 2,
        row * TILE + TILE // 2
    )


# ==================================================
# A* PATHFINDING
# ==================================================

def find_path(start, goal):

    if not is_open(*start) or not is_open(*goal):
        return []

    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    closed = set()

    while open_set:

        _, current = heapq.heappop(open_set)

        if current in closed:
            continue

        if current == goal:
            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            path.reverse()
            return path

        closed.add(current)

        col, row = current

        neighbors = [
            (col + 1, row),
            (col - 1, row),
            (col, row + 1),
            (col, row - 1)
        ]

        for neighbor in neighbors:

            if not is_open(*neighbor) or neighbor in closed:
                continue

            new_cost = g_score[current] + 1

            if new_cost < g_score.get(neighbor, float("inf")):

                came_from[neighbor] = current
                g_score[neighbor] = new_cost

                heuristic = (
                    abs(neighbor[0] - goal[0])
                    + abs(neighbor[1] - goal[1])
                )

                heapq.heappush(
                    open_set,
                    (new_cost + heuristic, neighbor)
                )

    return []


# ==================================================
# GAME STATE
# ==================================================

game_state = "menu"
difficulty = "PEZHMAN"

player_x = 135.0
player_y = 135.0

enemy_x = 1395.0
enemy_y = 855.0

PLAYER_SPEED = 240

enemy_path = []
path_goal = None

camera_x = 0
camera_y = 0

caught = False


def start_game():

    global player_x, player_y
    global enemy_x, enemy_y
    global enemy_path, path_goal
    global caught, game_state

    player_x = 135.0
    player_y = 135.0

    enemy_x = 1395.0
    enemy_y = 855.0

    enemy_path = []
    path_goal = None

    caught = False
    game_state = "game"


# ==================================================
# MUSIC
# ==================================================

def play_music_for_difficulty(mode):

    for sound in sounds.values():
        if sound:
            sound.stop()

    if mode == "HOSSEINI":
        sound = sounds["HOSSEINI"]
    else:
        sound = sounds["DEFAULT"]

    if sound:
        sound.volume = 0.8
        sound.loop = True
        sound.play()


play_music_for_difficulty("PEZHMAN")


# ==================================================
# COLLISION AND MOVEMENT
# ==================================================

def can_move(x, y, radius=17):

    points = [
        (x - radius, y),
        (x + radius, y),
        (x, y - radius),
        (x, y + radius)
    ]

    for px, py in points:
        col, row = world_to_tile(px, py)

        if not is_open(col, row):
            return False

    return True


def move_player(dx, dy):

    global player_x, player_y

    new_x = player_x + dx

    if can_move(new_x, player_y):
        player_x = new_x

    new_y = player_y + dy

    if can_move(player_x, new_y):
        player_y = new_y


# ==================================================
# ENEMY AI
# ==================================================

def move_enemy(dt):

    global enemy_x, enemy_y
    global enemy_path, path_goal

    enemy_tile = world_to_tile(enemy_x, enemy_y)
    player_tile = world_to_tile(player_x, player_y)

    if (
        not enemy_path
        or enemy_tile != enemy_path[0]
        or player_tile != path_goal
    ):
        enemy_path = find_path(enemy_tile, player_tile)
        path_goal = player_tile

    if not enemy_path:
        return

    if enemy_tile == player_tile:
        target_x = player_x
        target_y = player_y

    elif len(enemy_path) >= 2:
        target_x, target_y = tile_center(enemy_path[1])

    else:
        return

    dx = target_x - enemy_x
    dy = target_y - enemy_y

    distance = math.hypot(dx, dy)

    if distance < 1:
        return

    speed = enemies[difficulty]["speed"]
    step = min(speed * dt, distance)

    move_x = dx / distance * step
    move_y = dy / distance * step

    if can_move(enemy_x + move_x, enemy_y, 17):
        enemy_x += move_x

    if can_move(enemy_x, enemy_y + move_y, 17):
        enemy_y += move_y


# ==================================================
# KIVY GAME
# ==================================================

class HaghayeghGame(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.scale = 1
        self.offset_x = 0
        self.offset_y = 0

        self.joystick_active = False
        self.joystick_touch = None
        self.joystick_dx = 0
        self.joystick_dy = 0

        self.bind(size=self.redraw, pos=self.redraw)

        Clock.schedule_interval(self.update, 1 / FPS)

    # --------------------------------------------------
    # VIRTUAL SCREEN COORDINATES
    # --------------------------------------------------

    def calculate_viewport(self):

        self.scale = min(
            self.width / VIRTUAL_W,
            self.height / VIRTUAL_H
        )

        self.offset_x = (
            self.x + (self.width - VIRTUAL_W * self.scale) / 2
        )

        self.offset_y = (
            self.y + (self.height - VIRTUAL_H * self.scale) / 2
        )

    def screen_rect(self, x, y, w, h):

        sx = self.offset_x + x * self.scale
        sy = (
            self.offset_y
            + (VIRTUAL_H - y - h) * self.scale
        )

        return sx, sy, w * self.scale, h * self.scale

    def touch_to_virtual(self, touch):

        vx = (touch.x - self.offset_x) / self.scale

        vy = VIRTUAL_H - (
            (touch.y - self.offset_y) / self.scale
        )

        return vx, vy

    # --------------------------------------------------
    # DRAWING HELPERS
    # --------------------------------------------------

    def rect(self, color, x, y, w, h, radius=0,
             border=None, border_width=1):

        Color(*color)

        geometry = self.screen_rect(x, y, w, h)

        if radius:
            RoundedRectangle(
                pos=geometry[:2],
                size=geometry[2:],
                radius=[radius * self.scale]
            )
        else:
            Rectangle(
                pos=geometry[:2],
                size=geometry[2:]
            )

        if border:
            Color(*border)
            Line(
                rounded_rectangle=(
                    geometry[0],
                    geometry[1],
                    geometry[2],
                    geometry[3],
                    radius * self.scale
                ),
                width=border_width * self.scale
            )

    def text(self, value, x, y, size, color,
             bold=True, center=True):

        label = CoreLabel(
            text=str(value),
            font_size=size * self.scale,
            bold=bold
        )

        label.refresh()
        texture = label.texture

        if not texture:
            return

        w, h = texture.size

        if center:
            x -= w / (2 * self.scale)

        sx = self.offset_x + x * self.scale
        sy = self.offset_y + (
            VIRTUAL_H - y
        ) * self.scale - h

        Color(*color)
        Rectangle(
            texture=texture,
            pos=(sx, sy),
            size=(w, h)
        )

    def image(self, texture, x, y, w, h, radius=0):

        if not texture:
            return

        geometry = self.screen_rect(x, y, w, h)

        Color(1, 1, 1, 1)

        if radius:
            RoundedRectangle(
                texture=texture,
                pos=geometry[:2],
                size=geometry[2:],
                radius=[radius * self.scale]
            )
        else:
            Rectangle(
                texture=texture,
                pos=geometry[:2],
                size=geometry[2:]
            )

    def line(self, color, points, width=2):

        converted = []

        for x, y in points:
            converted.extend([
                self.offset_x + x * self.scale,
                self.offset_y + (VIRTUAL_H - y) * self.scale
            ])

        Color(*color)
        Line(
            points=converted,
            width=width * self.scale
        )

    def circle(self, color, x, y, radius):

        sx, sy, w, h = self.screen_rect(
            x - radius,
            y - radius,
            radius * 2,
            radius * 2
        )

        Color(*color)
        Ellipse(pos=(sx, sy), size=(w, h))

    # --------------------------------------------------
    # MENU BACKGROUND
    # --------------------------------------------------

    def draw_menu_background(self):

        self.rect((10/255, 10/255, 10/255, 1),
                  0, 0, VIRTUAL_W, VIRTUAL_H)

        portrait_width = VIRTUAL_W // 3

        for index, texture in enumerate(portrait_textures):

            x = index * portrait_width

            if texture:
                self.image(
                    texture,
                    x,
                    0,
                    portrait_width,
                    VIRTUAL_H
                )
            else:
                self.rect(
                    (35/255, 30/255, 25/255, 1),
                    x + 5, 5,
                    portrait_width - 10,
                    VIRTUAL_H - 10,
                    35
                )

        # Dark overlay
        self.rect(
            (0, 0, 0, 175/255),
            0, 0, VIRTUAL_W, VIRTUAL_H
        )

        self.line(
            (20/255, 15/255, 10/255, 1),
            [(portrait_width, 0),
             (portrait_width, VIRTUAL_H)],
            5
        )

        self.line(
            (20/255, 15/255, 10/255, 1),
            [(portrait_width * 2, 0),
             (portrait_width * 2, VIRTUAL_H)],
            5
        )

    # --------------------------------------------------
    # BUTTONS
    # --------------------------------------------------

    def draw_button(self, label, x, y, w, h):

        self.rect(
            (10/255, 8/255, 5/255, 1),
            x, y + 7, w, h, 25
        )

        self.rect(
            (45/255, 38/255, 27/255, 1),
            x, y, w, h, 25,
            (YELLOW[0]/255, YELLOW[1]/255,
             YELLOW[2]/255, 1),
            3
        )

        self.text(
            label,
            x + w / 2,
            y + h / 2 + 12,
            38,
            (WHITE[0]/255, WHITE[1]/255,
             WHITE[2]/255, 1)
        )

    # --------------------------------------------------
    # MAIN MENU
    # --------------------------------------------------

    def draw_menu(self):

        self.draw_menu_background()

        if logo_texture:
            self.image(
                logo_texture,
                VIRTUAL_W // 2 - 195,
                67,
                390,
                165,
                24
            )

        self.text(
            "HAGHAYEGH SHAHR FARSH",
            VIRTUAL_W // 2,
            310,
            72,
            (YELLOW[0]/255, YELLOW[1]/255,
             YELLOW[2]/255, 1)
        )

        self.draw_button(
            "START", VIRTUAL_W // 2 - 220,
            600, 440, 80
        )

        self.draw_button(
            "DIFFICULTY", VIRTUAL_W // 2 - 220,
            710, 440, 80
        )

        self.draw_button(
            "CASES", VIRTUAL_W // 2 - 220,
            820, 440, 80
        )

    # --------------------------------------------------
    # DIFFICULTY MENU
    # --------------------------------------------------

    def draw_difficulty(self):

        self.draw_menu_background()

        self.text(
            "SELECT DIFFICULTY",
            VIRTUAL_W // 2,
            190,
            72,
            (YELLOW[0]/255, YELLOW[1]/255,
             YELLOW[2]/255, 1)
        )

        options = [
            ("PEZHMAN MODE", "PEZHMAN"),
            ("HOSSEINI MODE", "HOSSEINI"),
            ("AASEF MODE", "AASEF"),
            ("MIRZAEE MODE", "MIRZAEE"),
            ("ZAADPOUR MODE", "ZAADPOUR")
        ]

        for index, (label, value) in enumerate(options):

            y = 290 + index * 115

            self.draw_button(
                label,
                VIRTUAL_W // 2 - 270,
                y,
                540,
                80
            )

            if difficulty == value:
                self.rect(
                    (RED[0]/255, RED[1]/255,
                     RED[2]/255, 1),
                    VIRTUAL_W // 2 - 274,
                    y - 4,
                    548,
                    88,
                    29,
                    border_width=4
                )

        self.draw_button(
            "BACK",
            VIRTUAL_W // 2 - 220,
            890,
            440,
            75
        )

    # --------------------------------------------------
    # CASES MENU
    # --------------------------------------------------

    def draw_cases(self):

        self.draw_menu_background()

        self.text(
            "STUDENTS",
            VIRTUAL_W // 2,
            230,
            72,
            (YELLOW[0]/255, YELLOW[1]/255,
             YELLOW[2]/255, 1)
        )

        names = [
            "Amir Hosseyn Ghiasi",
            "Pezhman Bazeghi",
            "Amir Hossein Zaadpour",
            "Saaed Jamali"
        ]

        for index, name in enumerate(names):
            self.text(
                name,
                VIRTUAL_W // 2,
                390 + index * 90,
                38,
                (WHITE[0]/255, WHITE[1]/255,
                 WHITE[2]/255, 1)
            )

        self.draw_button(
            "BACK",
            VIRTUAL_W // 2 - 220,
            850,
            440,
            75
        )

    # --------------------------------------------------
    # WORLD
    # --------------------------------------------------

    def draw_world(self):

        self.rect(
            (135/255, 125/255, 85/255, 1),
            0, 0, VIRTUAL_W, VIRTUAL_H
        )

        for row in range(ROWS):

            for col in range(COLS):

                x = col * TILE - camera_x
                y = row * TILE - camera_y

                if (
                    x > VIRTUAL_W or y > VIRTUAL_H
                    or x + TILE < 0 or y + TILE < 0
                ):
                    continue

                if world[row][col] == "1":

                    self.rect(
                        (45/255, 38/255, 25/255, 1),
                        x + 3, y + 8,
                        TILE - 6, TILE - 6, 15
                    )

                    self.rect(
                        (75/255, 65/255, 42/255, 1),
                        x + 3, y + 3,
                        TILE - 6, TILE - 6, 15,
                        (115/255, 98/255, 60/255, 1),
                        3
                    )

                    self.line(
                        (135/255, 115/255, 75/255, 1),
                        [
                            (x + 20, y + 11),
                            (x + TILE - 20, y + 11)
                        ],
                        2
                    )

                else:

                    self.rect(
                        (165/255, 155/255, 105/255, 1),
                        x + 3, y + 3,
                        TILE - 6, TILE - 6, 14,
                        (155/255, 145/255, 98/255, 1),
                        1
                    )

                    random.seed(row * 1000 + col)

                    for _ in range(5):

                        px = x + random.randint(12, TILE - 12)
                        py = y + random.randint(12, TILE - 12)

                        self.circle(
                            (150/255, 140/255, 95/255, 1),
                            px, py, 2
                        )

        random.seed()

    # --------------------------------------------------
    # CHARACTERS
    # --------------------------------------------------

    def draw_character(self, texture, x, y, fallback):

        screen_x = x - camera_x
        screen_y = y - camera_y

        self.circle(
            (45/255, 40/255, 25/255, 1),
            screen_x,
            screen_y + 30,
            16
        )

        if texture:
            self.image(
                texture,
                screen_x - 32.5,
                screen_y - 32.5,
                65,
                65,
                20
            )
        else:
            self.circle(
                (fallback[0]/255, fallback[1]/255,
                 fallback[2]/255, 1),
                screen_x, screen_y, 30
            )

    # --------------------------------------------------
    # GAME OVER
    # --------------------------------------------------

    def draw_game_over(self):

        self.rect(
            (0, 0, 0, 220/255),
            0, 0, VIRTUAL_W, VIRTUAL_H
        )

        panel_x = VIRTUAL_W // 2 - 600
        panel_y = 300

        self.rect(
            (0, 0, 0, 1),
            panel_x, panel_y + 8,
            1200, 430, 45
        )

        self.rect(
            (28/255, 22/255, 18/255, 1),
            panel_x, panel_y,
            1200, 430, 45,
            (125/255, 75/255, 45/255, 1),
            4
        )

        self.text(
            difficulty + " FOUND YOU",
            VIRTUAL_W // 2,
            390,
            72,
            (RED[0]/255, RED[1]/255,
             RED[2]/255, 1)
        )

        self.text(
            enemies[difficulty]["dialogue"],
            VIRTUAL_W // 2,
            510,
            45,
            (WHITE[0]/255, WHITE[1]/255,
             WHITE[2]/255, 1)
        )

        self.text(
            "TAP TO RETURN TO MENU",
            VIRTUAL_W // 2,
            650,
            38,
            (YELLOW[0]/255, YELLOW[1]/255,
             YELLOW[2]/255, 1)
        )

    # --------------------------------------------------
    # GAME DRAWING
    # --------------------------------------------------

    def draw_game(self):

        global camera_x, camera_y

        if MAP_WIDTH < VIRTUAL_W:
            camera_x = (MAP_WIDTH - VIRTUAL_W) // 2
        else:
            camera_x = max(
                0,
                min(
                    player_x - VIRTUAL_W // 2,
                    MAP_WIDTH - VIRTUAL_W
                )
            )

        if MAP_HEIGHT < VIRTUAL_H:
            camera_y = (MAP_HEIGHT - VIRTUAL_H) // 2
        else:
            camera_y = max(
                0,
                min(
                    player_y - VIRTUAL_H // 2,
                    MAP_HEIGHT - VIRTUAL_H
                )
            )

        self.draw_world()

        self.draw_character(
            enemy_textures[difficulty],
            enemy_x, enemy_y, RED
        )

        self.draw_character(
            player_texture,
            player_x, player_y, (40, 100, 220)
        )

        self.rect(
            (35/255, 30/255, 20/255, 1),
            20, 20, 300, 55, 20,
            (YELLOW[0]/255, YELLOW[1]/255,
             YELLOW[2]/255, 1),
            2
        )

        self.text(
            difficulty + " MODE",
            170,
            58,
            27,
            (WHITE[0]/255, WHITE[1]/255,
             WHITE[2]/255, 1)
        )

        self.draw_joystick()

        if caught:
            self.draw_game_over()

    # --------------------------------------------------
    # TOUCH JOYSTICK
    # --------------------------------------------------

    def draw_joystick(self):

        cx = 180
        cy = 870

        self.circle(
            (0.05, 0.05, 0.05, 0.55),
            cx, cy, 105
        )

        self.circle(
            (0.55, 0.48, 0.30, 0.8),
            cx + self.joystick_dx * 65,
            cy + self.joystick_dy * 65,
            43
        )

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def on_touch_down(self, touch):

        global game_state, difficulty

        vx, vy = self.touch_to_virtual(touch)

        if game_state == "menu":

            if 600 <= vy <= 680 and 740 <= vx <= 1180:
                start_game()

            elif 710 <= vy <= 790 and 740 <= vx <= 1180:
                game_state = "difficulty"

            elif 820 <= vy <= 900 and 740 <= vx <= 1180:
                game_state = "cases"

            self.redraw()
            return True

        if game_state == "difficulty":

            options = [
                "PEZHMAN",
                "HOSSEINI",
                "AASEF",
                "MIRZAEE",
                "ZAADPOUR"
            ]

            for index, value in enumerate(options):

                y = 290 + index * 115

                if (
                    y <= vy <= y + 80
                    and 650 <= vx <= 1270
                ):
                    difficulty = value
                    play_music_for_difficulty(difficulty)

            if 890 <= vy <= 965 and 740 <= vx <= 1180:
                game_state = "menu"

            self.redraw()
            return True

        if game_state == "cases":

            if 850 <= vy <= 925 and 740 <= vx <= 1180:
                game_state = "menu"

            self.redraw()
            return True

        if game_state == "game":

            if caught:
                game_state = "menu"
                self.redraw()
                return True

            # Joystick is on the lower-left side.
            if vx < 430 and vy > 650:
                self.joystick_active = True
                self.joystick_touch = touch.uid
                self.update_joystick(vx, vy)
                return True

            return True

        return True

    def update_joystick(self, vx, vy):

        dx = vx - 180
        dy = vy - 870

        length = math.hypot(dx, dy)

        if length > 100:
            dx = dx / length * 100
            dy = dy / length * 100

        self.joystick_dx = dx / 100
        self.joystick_dy = -dy / 100

    def on_touch_move(self, touch):

        if (
            self.joystick_active
            and touch.uid == self.joystick_touch
        ):
            vx, vy = self.touch_to_virtual(touch)
            self.update_joystick(vx, vy)
            return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):

        if (
            self.joystick_active
            and touch.uid == self.joystick_touch
        ):
            self.joystick_active = False
            self.joystick_touch = None
            self.joystick_dx = 0
            self.joystick_dy = 0
            return True

        return super().on_touch_up(touch)

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update(self, dt):

        global caught

        dt = min(dt, 0.05)

        if game_state == "game" and not caught:

            dx = self.joystick_dx * PLAYER_SPEED * dt
            dy = self.joystick_dy * PLAYER_SPEED * dt

            if dx and dy:
                dx *= 0.70710678
                dy *= 0.70710678

            move_player(dx, dy)
            move_enemy(dt)

            distance = math.hypot(
                player_x - enemy_x,
                player_y - enemy_y
            )

            if distance < 45:
                caught = True

        self.redraw()

    # --------------------------------------------------
    # RENDER
    # --------------------------------------------------

    def redraw(self, *args):

        self.calculate_viewport()

        self.canvas.clear()

        with self.canvas:

            if game_state == "menu":
                self.draw_menu()

            elif game_state == "difficulty":
                self.draw_difficulty()

            elif game_state == "cases":
                self.draw_cases()

            elif game_state == "game":
                self.draw_game()


# ==================================================
# APP
# ==================================================

class HaghayeghApp(App):

    def build(self):
        self.title = "Haghayegh Shahr Farsh"
        return HaghayeghGame()


if __name__ == "__main__":
    HaghayeghApp().run()
