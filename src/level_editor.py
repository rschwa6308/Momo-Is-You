# Standalone GUI Applet for creating levels

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
def update_screen(screen, board, viewport_rect, redraw_board=True, selected_entity=None, cursor_position=None):
    global board_layer_cache
    if redraw_board or board_layer_cache is None:
        board_layer = pygame.Surface((viewport_rect.width, viewport_rect.height))
        draw_board_onto_viewport(board_layer, board, VIEWPORT_BACKGROUND_COLOR, GRID_COLOR)
        board_layer_cache = board_layer.copy()
    else:
        board_layer = board_layer_cache
    screen.blit(board_layer, viewport_rect)

    if selected_entity and cursor_position:
        board_width, board_height = len(board[0]), len(board)
        tile_size_px = min(viewport_rect.width // board_width, viewport_rect.height // board_height)
        img = get_entity_image(selected_entity, tile_size_px, VIEWPORT_BACKGROUND_COLOR)
        draw_pos = (cursor_position[0] - tile_size_px // 2, cursor_position[1] - tile_size_px // 2)
        screen.blit(img, draw_pos)

    pygame.display.update(viewport_rect)


# Size the viewport to both preserve level.board's aspect ratio and respect VIEWPORT_MIN_PADDING
def get_viewport_rect(screen_width_px, screen_height_px, board_width_tiles, board_height_tiles):
    width_ratio = (screen_width_px - VIEWPORT_MIN_PADDING * 2) // board_width_tiles
    height_ratio = (screen_height_px - VIEWPORT_MIN_PADDING * 2) // board_height_tiles
    pixels_per_tile = min(width_ratio, height_ratio)

    viewport_width = board_width_tiles * pixels_per_tile
    viewport_height = board_height_tiles * pixels_per_tile

    return pygame.Rect(
        ((screen_width_px - viewport_width) // 2, (screen_height_px - viewport_height) // 2),  # centered in screen
        (viewport_width, viewport_height)
    )


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



def perform_click(pos_px, viewport_rect, board_dims, selected):
    pass


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
                viewport_rect = get_viewport_rect(new_screen_width, new_screen_height, board_width, board_height)
                update_screen(screen, board, viewport_rect)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # discard event if click was outside viewport
                    if not viewport_rect.collidepoint(event.pos):
                        continue

                    x_tiles, y_tiles = pixels_to_tiles(*event.pos, viewport_rect, board_width, board_height)

                    # print("CLICK:\t", (x_tiles, y_tiles))
                    clicked_tile = board[y_tiles][x_tiles]
                    if selected_entity is None:
                        # select an entity and redraw
                        if len(clicked_tile) > 0:
                            selected_entity = clicked_tile.pop()   # remove top entity
                            update_screen(screen, board, viewport_rect, redraw_board=True, selected_entity=selected_entity, cursor_position=event.pos)

                    else:
                        # deselect the entity and redraw
                        clicked_tile.append(selected_entity)
                        selected_entity = None
                        update_screen(screen, board, viewport_rect)
            
            elif event.type == pygame.MOUSEMOTION:
                if selected_entity:
                    if viewport_rect.collidepoint(event.pos):
                        update_screen(screen, board, viewport_rect, redraw_board=False, selected_entity=selected_entity, cursor_position=event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    write_level_start("test_output.lvl", board)
                    print("level saved!")
        


if __name__ == "__main__":
    run_editor(level_starts[0])
