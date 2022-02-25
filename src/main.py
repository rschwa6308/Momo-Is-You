# Micah Johnson and Russell Schwartz
# August 2019

import os
os.environ['pg_HIDE_SUPPORT_PROMPT'] = "hide"   # grrr

from engine import Level
from levels import levels
from ui_helpers import *

# --- UI-Related Constants --- #
STARTING_SCREEN_WIDTH, STARTING_SCREEN_HEIGHT = 800, 600  # starting dimensions of screen (px)
MIN_SCREEN_WIDTH = 160
MIN_SCREEN_HEIGHT = 120
VIEWPORT_MIN_PADDING = 50  # minimum viewport edge padding (px)

SCREEN_BACKGROUND_COLOR = (25, 25, 32)
VIEWPORT_BACKGROUND_COLOR = (15, 15, 15)

TARGET_FPS = 60
INPUT_REPEAT_BUFFER_MS = 300   # time the key must be held for before entering repeat mode
INPUT_REPEAT_PERIOD_MS = 100   # time between registered inputs when in repeat mode


key_map = {
    pg.K_UP: Level.UP,
    pg.K_DOWN: Level.DOWN,
    pg.K_LEFT: Level.LEFT,
    pg.K_RIGHT: Level.RIGHT,

    pg.K_w: Level.UP,
    pg.K_s: Level.DOWN,
    pg.K_a: Level.LEFT,
    pg.K_d: Level.RIGHT,

    pg.K_SPACE: Level.WAIT,
    pg.K_z: Level.UNDO,
    pg.K_r: Level.RESTART
}


# Draw the level onto a fresh viewport surface, blit it to the screen, and flip the display
def update_screen(screen, level, viewport_rect):
    viewport = pg.Surface((viewport_rect.width, viewport_rect.height))
    draw_board_onto_viewport(viewport, level.board, VIEWPORT_BACKGROUND_COLOR)
    screen.blit(viewport, viewport_rect)
    pg.display.update(viewport_rect)


# Size the viewport to both preserve level.board's aspect ratio and respect VIEWPORT_MIN_PADDING
def get_viewport_rect(screen_width_px, screen_height_px, level_width_tiles, level_height_tiles):
    width_ratio = (screen_width_px - VIEWPORT_MIN_PADDING * 2) // level_width_tiles
    height_ratio = (screen_height_px - VIEWPORT_MIN_PADDING * 2) // level_height_tiles
    pixels_per_tile = min(width_ratio, height_ratio)

    viewport_width = level_width_tiles * pixels_per_tile
    viewport_height = level_height_tiles * pixels_per_tile

    return pg.Rect(
        ((screen_width_px - viewport_width) // 2, (screen_height_px - viewport_height) // 2),  # centered in screen
        (viewport_width, viewport_height)
    )


def get_initialized_screen(screen_width_px, screen_height_px):
    new_screen = pg.display.set_mode((screen_width_px, screen_height_px), pg.RESIZABLE)
    new_screen.fill(SCREEN_BACKGROUND_COLOR)
    return new_screen


# Initializes display, listens for keypress's, calls engine API methods, and handles window re-size events
def play_level(level):
    # initialize screen; VIDEORESIZE event is generated immediately
    screen = get_initialized_screen(STARTING_SCREEN_WIDTH, STARTING_SCREEN_HEIGHT)

    # initialize keypress vars
    currently_pressed = None
    last_input_timestamp = 0  # ms
    repeating_inputs = False

    # store the input timestamp, send the input to the level, update the screen
    def process_keypress(key):
        nonlocal last_input_timestamp
        last_input_timestamp = pg.time.get_ticks()
        # only update the screen when the board state changes
        if level.process_input(key_map[key]):
            update_screen(screen, level, viewport_rect)

    # restore the initial VIDEORESIZE event (removed in pg 2.1)
    pg.event.post(pg.event.Event(
        pg.VIDEORESIZE,
        {"w": STARTING_SCREEN_WIDTH, "h": STARTING_SCREEN_HEIGHT}
    ))

    # main game loop
    clock = pg.time.Clock()
    level_alive = True
    while level_alive:
        clock.tick(TARGET_FPS)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                level_alive = False
            elif event.type == pg.KEYDOWN:
                if event.key in key_map.keys():
                    process_keypress(event.key)
                    currently_pressed = event.key
            elif event.type == pg.KEYUP:
                if event.key == currently_pressed:
                    currently_pressed = None
                    repeating_inputs = False
            elif event.type == pg.VIDEORESIZE:
                new_screen_width = max(event.w, MIN_SCREEN_WIDTH)
                new_screen_height = max(event.h, MIN_SCREEN_HEIGHT)
                screen = get_initialized_screen(new_screen_width, new_screen_height)
                pg.display.update()
                viewport_rect = get_viewport_rect(new_screen_width, new_screen_height, level.width, level.height)
                update_screen(screen, level, viewport_rect)

        # handle repeat mode inputs
        if currently_pressed is not None:
            current_timestamp = pg.time.get_ticks()

            if current_timestamp - last_input_timestamp > INPUT_REPEAT_BUFFER_MS:
                repeating_inputs = True

            if repeating_inputs and current_timestamp - last_input_timestamp > INPUT_REPEAT_PERIOD_MS:
                process_keypress(currently_pressed)

        if level.has_won:
            print("\nCongrats! You beat the level!")
            pg.time.wait(1000)
            level_alive = False


if __name__ == "__main__":
    # load a test level (with logging disabled)
    test_level = Level(levels[0], logging=False)
    play_level(test_level)
