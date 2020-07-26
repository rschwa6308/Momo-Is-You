# Micah Johnson and Russell Schwartz
# August 2019

from engine import Level
from levels import level_starts
from ui_helpers import *

# --- UI-Related Constants --- #
STARTING_SCREEN_WIDTH, STARTING_SCREEN_HEIGHT = 800, 600  # starting dimensions of screen (px)
MIN_SCREEN_WIDTH = 160
MIN_SCREEN_HEIGHT = 120
VIEWPORT_MIN_PADDING = 50  # minimum viewport edge padding (px)

SCREEN_BACKGROUND_COLOR = (25, 25, 32)
VIEWPORT_BACKGROUND_COLOR = (15, 15, 15)

TARGET_FPS = 60
INPUT_REPEAT_BUFFER_MS = 120  # time between registered inputs when key is held

key_map = {
    pygame.K_UP: Level.UP,
    pygame.K_DOWN: Level.DOWN,
    pygame.K_LEFT: Level.LEFT,
    pygame.K_RIGHT: Level.RIGHT,
    pygame.K_SPACE: Level.WAIT,
    pygame.K_z: Level.UNDO,
    pygame.K_r: Level.RESTART
}


# Draw the level onto a fresh viewport surface, blit it to the screen, and flip the display
def update_screen(screen, level, viewport_rect):
    viewport = pygame.Surface((viewport_rect.width, viewport_rect.height))
    draw_board_onto_viewport(viewport, level.board, VIEWPORT_BACKGROUND_COLOR)
    screen.blit(viewport, viewport_rect)
    pygame.display.update(viewport_rect)


# Size the viewport to both preserve level.board's aspect ratio and respect VIEWPORT_MIN_PADDING
def get_viewport_rect(screen_width_px, screen_height_px, level_width_tiles, level_height_tiles):
    width_ratio = (screen_width_px - VIEWPORT_MIN_PADDING * 2) // level_width_tiles
    height_ratio = (screen_height_px - VIEWPORT_MIN_PADDING * 2) // level_height_tiles
    pixels_per_tile = min(width_ratio, height_ratio)

    viewport_width = level_width_tiles * pixels_per_tile
    viewport_height = level_height_tiles * pixels_per_tile

    return pygame.Rect(
        ((screen_width_px - viewport_width) // 2, (screen_height_px - viewport_height) // 2),  # centered in screen
        (viewport_width, viewport_height)
    )


def get_initialized_screen(screen_width_px, screen_height_px):
    new_screen = pygame.display.set_mode((screen_width_px, screen_height_px), pygame.RESIZABLE)
    new_screen.fill(SCREEN_BACKGROUND_COLOR)
    return new_screen


# Initializes display, listens for keypress's, calls engine API methods, and handles window re-size events
def play_level(level):
    # initialize screen; VIDEORESIZE event is generated immediately
    screen = get_initialized_screen(STARTING_SCREEN_WIDTH, STARTING_SCREEN_HEIGHT)

    # initialize keypress vars
    currently_pressed = None
    last_input_timestamp = 0  # ms

    # main game loop
    clock = pygame.time.Clock()
    level_alive = True
    while level_alive:
        clock.tick(TARGET_FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                level_alive = False
            elif event.type == pygame.KEYDOWN:
                if event.key in key_map.keys():
                    currently_pressed = event.key
            elif event.type == pygame.KEYUP:
                if event.key == currently_pressed:
                    currently_pressed = None
            elif event.type == pygame.VIDEORESIZE:
                new_screen_width = max(event.w, MIN_SCREEN_WIDTH)
                new_screen_height = max(event.h, MIN_SCREEN_HEIGHT)
                screen = get_initialized_screen(new_screen_width, new_screen_height)
                pygame.display.update()
                viewport_rect = get_viewport_rect(new_screen_width, new_screen_height, level.width, level.height)
                update_screen(screen, level, viewport_rect)

        if currently_pressed is not None:
            current_timestamp = pygame.time.get_ticks()
            if current_timestamp - last_input_timestamp > INPUT_REPEAT_BUFFER_MS:
                last_input_timestamp = current_timestamp
                level.process_input(key_map[currently_pressed])
                update_screen(screen, level, viewport_rect)  # TODO: only call this when needed

        if level.has_won:
            print("\nCongrats! You beat the level!")
            pygame.time.wait(1000)
            level_alive = False


if __name__ == "__main__":
    test_level = Level(level_starts[0])
    play_level(test_level)
