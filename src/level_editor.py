# Standalone GUI Applet for creating levels

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

from ui_helpers import *
from levels import level_starts, write_level_start


# --- UI-Related Constants --- #
STARTING_SCREEN_WIDTH, STARTING_SCREEN_HEIGHT = 800, 600  # starting dimensions of screen (px)
MIN_SCREEN_WIDTH = 160
MIN_SCREEN_HEIGHT = 120
VIEWPORT_MIN_PADDING = 50  # minimum viewport edge padding (px)

SCREEN_BACKGROUND_COLOR = (25, 25, 32)
VIEWPORT_BACKGROUND_COLOR = (15, 15, 15)
GRID_COLOR = (0, 80, 90, 127)

TARGET_FPS = 60


# Draw the level onto a fresh viewport surface, render UI elements, blit them to the screen, and flip the display
# only re-draws the board layer if corresponding flag is set; otherwise, cached surface is used
def update_screen(screen, board, main_viewport_rect, palette_viewport_rect, redraw_board=True, selected_entity=None, cursor_position=None):
    screen.fill(SCREEN_BACKGROUND_COLOR)

    global board_layer_cache
    if redraw_board or board_layer_cache is None:
        board_layer = pygame.Surface((main_viewport_rect.width, main_viewport_rect.height))
        draw_board_onto_viewport(board_layer, board, VIEWPORT_BACKGROUND_COLOR, GRID_COLOR)
        board_layer_cache = board_layer.copy()
    else:
        board_layer = board_layer_cache
    screen.blit(board_layer, main_viewport_rect)

    palette_layer = pygame.Surface((palette_viewport_rect.width, palette_viewport_rect.height))
    palette_layer.fill(VIEWPORT_BACKGROUND_COLOR)
    screen.blit(palette_layer, palette_viewport_rect)

    if selected_entity and cursor_position:
        board_width, board_height = len(board[0]), len(board)
        tile_size_px = min(main_viewport_rect.width // board_width, main_viewport_rect.height // board_height)
        img = get_entity_image(selected_entity, tile_size_px, VIEWPORT_BACKGROUND_COLOR)
        draw_pos = (cursor_position[0] - tile_size_px // 2, cursor_position[1] - tile_size_px // 2)
        screen.blit(img, draw_pos)

    pygame.display.update()


# Size the 'root', 'main', and 'palette' viewports to both preserve level.board's aspect ratio and respect VIEWPORT_MIN_PADDING
# Returns (root_viewport_rect, main_viewport_rect, palette_rect)
def get_viewport_rects(screen_width_px, screen_height_px, board_width_tiles, board_height_tiles):
    width_ratio = (screen_width_px - VIEWPORT_MIN_PADDING * 2) // (board_width_tiles + 4)
    height_ratio = (screen_height_px - VIEWPORT_MIN_PADDING * 2) // board_height_tiles
    pixels_per_tile = min(width_ratio, height_ratio)

    root_viewport_width = (board_width_tiles + 4) * pixels_per_tile
    root_viewport_height = board_height_tiles * pixels_per_tile

    root_viewport_rect = pygame.Rect(
        ((screen_width_px - root_viewport_width) // 2, (screen_height_px - root_viewport_height) // 2),  # centered in screen
        (root_viewport_width, root_viewport_height)
    )

    palette_viewport_rect = pygame.Rect(
        (root_viewport_rect.left, root_viewport_rect.top),
        (3 * pixels_per_tile, root_viewport_height)
    )

    main_viewport_rect = pygame.Rect(
        (root_viewport_rect.left + 4 * pixels_per_tile, root_viewport_rect.top),
        (board_width_tiles * pixels_per_tile, root_viewport_height)
    )

    return (root_viewport_rect, main_viewport_rect, palette_viewport_rect)


def get_initialized_screen(screen_width_px, screen_height_px):
    new_screen = pygame.display.set_mode((screen_width_px, screen_height_px), pygame.RESIZABLE)
    new_screen.fill(SCREEN_BACKGROUND_COLOR)
    return new_screen


# Takes a screen location in pixels and returns the corresponding board location
def pixels_to_tiles(x_px, y_px, viewport_rect, board_width_tiles, board_height_tiles):
    x_px -= viewport_rect.left
    y_px -= viewport_rect.top

    x_tiles = int(float(x_px) / viewport_rect.width * board_width_tiles)
    y_tiles = int(float(y_px) / viewport_rect.height * board_height_tiles)

    return x_tiles, y_tiles


# Initializes display, listens for keypress's, and handles window re-size events
def run_editor(board=None):
    # initialize screen; VIDEORESIZE event is generated immediately
    screen = get_initialized_screen(STARTING_SCREEN_WIDTH, STARTING_SCREEN_HEIGHT)
    board_layer_cache = None

    if board is None:
        board = [[[] for _ in range(21)] for _ in range(15)]

    board_width, board_height = len(board[0]), len(board)

    selected_entity = None

    # main game loop
    clock = pygame.time.Clock()
    editor_alive = True
    while editor_alive:
        clock.tick(TARGET_FPS)

        # process input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                editor_alive = False
            
            elif event.type == pygame.VIDEORESIZE:
                new_screen_width = max(event.w, MIN_SCREEN_WIDTH)
                new_screen_height = max(event.h, MIN_SCREEN_HEIGHT)
                screen = get_initialized_screen(new_screen_width, new_screen_height)
                pygame.display.update()
                root_viewport_rect, main_viewport_rect, palette_viewport_rect =\
                    get_viewport_rects(new_screen_width, new_screen_height, board_width, board_height)
                update_screen(screen, board, main_viewport_rect, palette_viewport_rect)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # discard event if click was outside viewport
                    if not main_viewport_rect.collidepoint(event.pos):
                        continue

                    x_tiles, y_tiles = pixels_to_tiles(*event.pos, main_viewport_rect, board_width, board_height)

                    # print("CLICK:\t", (x_tiles, y_tiles))
                    clicked_tile = board[y_tiles][x_tiles]
                    if selected_entity is None:
                        # select an entity and redraw
                        if len(clicked_tile) > 0:
                            selected_entity = clicked_tile.pop()   # remove top entity
                            update_screen(screen, board, main_viewport_rect, palette_viewport_rect, redraw_board=True, selected_entity=selected_entity, cursor_position=event.pos)

                    else:
                        # deselect the entity and redraw
                        clicked_tile.append(selected_entity)
                        selected_entity = None
                        update_screen(screen, board, main_viewport_rect, palette_viewport_rect)
            
            elif event.type == pygame.MOUSEMOTION:
                if selected_entity:
                    if main_viewport_rect.collidepoint(event.pos):
                        update_screen(screen, board, main_viewport_rect, palette_viewport_rect, redraw_board=False, selected_entity=selected_entity, cursor_position=event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    write_level_start("test_output.lvl", board)
                    print("level saved!")
        

if __name__ == "__main__":
    run_editor(level_starts[0])
