# Standalone GUI Applet for creating levels

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

from multiprocessing import Process

from ui_helpers import *
from levels import levels, read_level, write_level, LEVELS_DIR
from main import play_level
from engine import Level, board_copy


# --- UI-Related Constants --- #
STARTING_SCREEN_WIDTH, STARTING_SCREEN_HEIGHT = 1000, 600  # starting dimensions of screen (px)
MIN_SCREEN_WIDTH = 160
MIN_SCREEN_HEIGHT = 120
VIEWPORT_MIN_PADDING = 50  # minimum viewport edge padding (px)

SCREEN_BACKGROUND_COLOR = (25, 25, 32)
VIEWPORT_BACKGROUND_COLOR = (15, 15, 15)
GRID_COLOR = (0, 80, 90, 127)

TARGET_FPS = 60

FILE_DIALOG_OPTIONS = {         # https://docs.python.org/3.9/library/dialog.html#native-load-save-dialogs
    "initialdir": LEVELS_DIR,
    "filetypes": [("Level Files", ".lvl")],
    "defaultextension": ".lvl"
}


# --- Level-Related Constants --- #
# the layout of entities in the palette (must be rectangular)
PALETTE_LAYOUT = [
    [Nouns.MOMO, Objects.MOMO],
    [Nouns.WALL, Objects.WALL],
    [Nouns.ROCK, Objects.ROCK],
    [Nouns.FLAG, Objects.FLAG],
    [Nouns.WATER, Objects.WATER],
    [None, None],
    [Adjectives.YOU, Adjectives.WIN],
    [Adjectives.STOP, Adjectives.PUSH],
    [Adjectives.DEFEAT, Adjectives.SINK],
    [None, None],
    [Verbs.IS, Verbs.HAS]
]

PALETTE_WIDTH = len(PALETTE_LAYOUT[0])
PALETTE_HEIGHT = len(PALETTE_LAYOUT)

# build palette board for easy rendering purposes (None -> empty cell)
PALETTE_BOARD = [
    [[e] if e else [] for e in row]
    for row in PALETTE_LAYOUT
]

# Valid board size ranges (inclusive)
BOARD_WIDTH_RANGE = (5, 35)
BOARD_HEIGHT_RANGE = (5, 25)

# Size of the default empty board
BOARD_DEFAULT_DIMS = (15, 12)


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
    draw_board_onto_viewport(palette_layer, PALETTE_BOARD, VIEWPORT_BACKGROUND_COLOR)

    screen.blit(palette_layer, palette_viewport_rect)

    if selected_entity and cursor_position:
        board_width, board_height = len(board[0]), len(board)
        tile_size_px = min(main_viewport_rect.width // board_width, main_viewport_rect.height // board_height)
        img = get_entity_image(selected_entity, tile_size_px)
        draw_pos = (cursor_position[0] - tile_size_px // 2, cursor_position[1] - tile_size_px // 2)
        screen.blit(img, draw_pos)

    pygame.display.update()


# Size the 'root', 'main', and 'palette' viewports to both preserve level.board's aspect ratio and respect VIEWPORT_MIN_PADDING
# Returns (root_viewport_rect, main_viewport_rect, palette_rect)
def get_viewport_rects(screen_width_px, screen_height_px, board_width_tiles, board_height_tiles):
    width_ratio = (screen_width_px - VIEWPORT_MIN_PADDING * 2) // (board_width_tiles + PALETTE_WIDTH + 1)
    height_ratio = (screen_height_px - VIEWPORT_MIN_PADDING * 2) // board_height_tiles
    pixels_per_tile = min(width_ratio, height_ratio)

    root_viewport_width = (board_width_tiles + PALETTE_WIDTH + 1) * pixels_per_tile
    root_viewport_height = board_height_tiles * pixels_per_tile

    root_viewport_rect = pygame.Rect(
        ((screen_width_px - root_viewport_width) // 2, (screen_height_px - root_viewport_height) // 2),  # centered in screen
        (root_viewport_width, root_viewport_height)
    )

    # calculate palette tile size (cannot be larger than main's)
    pixels_per_tile_palette = root_viewport_height // PALETTE_HEIGHT
    pixels_per_tile_palette = min(pixels_per_tile_palette, pixels_per_tile)
    
    palette_viewport_width = pixels_per_tile_palette * PALETTE_WIDTH
    palette_viewport_height = pixels_per_tile_palette * PALETTE_HEIGHT

    palette_viewport_rect = pygame.Rect(
        (root_viewport_rect.left, root_viewport_rect.top + (root_viewport_height - palette_viewport_height) // 2),
        (palette_viewport_width, palette_viewport_height)
    )

    main_viewport_rect = pygame.Rect(
        (root_viewport_rect.left + pixels_per_tile_palette * PALETTE_WIDTH + pixels_per_tile, root_viewport_rect.top),
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


# Takes a screen location in pixels and returns the corresponding palette location
def pixels_to_tiles_palette(x_px, y_px, viewport_rect, palette_width_tiles, palette_height_tiles):
    x_px -= viewport_rect.left
    y_px -= viewport_rect.top

    x_tiles = int(float(x_px) / viewport_rect.width * palette_width_tiles)
    y_tiles = int(float(y_px) / viewport_rect.height * palette_height_tiles)

    return x_tiles, y_tiles


# Initializes display, listens for keypress's, and handles window re-size events
def run_editor(board=None):
    level_filename = None

    board_width, board_height = None, None
    root_viewport_rect, main_viewport_rect, palette_viewport_rect = None, None, None

    # initialize screen; VIDEORESIZE event is generated immediately
    screen = get_initialized_screen(STARTING_SCREEN_WIDTH, STARTING_SCREEN_HEIGHT)
    board_layer_cache = None

    if board is None:
        board = [[[] for _ in range(BOARD_DEFAULT_DIMS[0])] for _ in range(BOARD_DEFAULT_DIMS[1])]

    selected_entity = None

    key_mods = pygame.key.get_mods()

    board_save_state = board_copy(board)

    playtest_process = None

    # discard selected entity and update screen (if CAPS-LOCK is not enabled)
    def discard_selected_item():
        nonlocal selected_entity
        nonlocal root_viewport_rect, main_viewport_rect, palette_viewport_rect
        if selected_entity:
            if not key_mods & pygame.KMOD_CAPS:
                # discard selected entity
                selected_entity = None
                update_screen(screen, board, main_viewport_rect, palette_viewport_rect)
            else:
                # keep selected entity
                update_screen(screen, board, main_viewport_rect, palette_viewport_rect, redraw_board=True, selected_entity=selected_entity, cursor_position=event.pos)
    
    # recalculate board dimensions, recalculate viewports, and update screen
    def refresh_layout():
        nonlocal board_width, board_height
        board_width, board_height = len(board[0]), len(board)

        nonlocal root_viewport_rect, main_viewport_rect, palette_viewport_rect
        root_viewport_rect, main_viewport_rect, palette_viewport_rect =\
            get_viewport_rects(new_screen_width, new_screen_height, board_width, board_height)
        update_screen(screen, board, main_viewport_rect, palette_viewport_rect)
    
    # update window caption based off level_filename
    def refresh_caption():
        if level_filename:
            caption = level_filename
        else:
            caption = "~ Unsaved Level ~"
        pygame.display.set_caption(caption)

    refresh_caption()

    # main game loop
    clock = pygame.time.Clock()
    editor_alive = True
    while editor_alive:
        clock.tick(TARGET_FPS)

        # process input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if board_save_state != board:
                    # if board_save_state is None or any(any(row) for row in board):
                    if not ask_yes_no("Level Editor", "You have unsaved work. Are you sure you want to quit?"):
                        continue
                editor_alive = False
            
            elif event.type == pygame.VIDEORESIZE:
                new_screen_width = max(event.w, MIN_SCREEN_WIDTH)
                new_screen_height = max(event.h, MIN_SCREEN_HEIGHT)
                screen = get_initialized_screen(new_screen_width, new_screen_height)
                refresh_layout()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # handle main viewport clicks
                    if main_viewport_rect.collidepoint(event.pos):
                        x_tiles, y_tiles = pixels_to_tiles(*event.pos, main_viewport_rect, board_width, board_height)
                        clicked_tile = board[y_tiles][x_tiles]
                        if selected_entity is None:
                            # select an entity and redraw
                            if len(clicked_tile) > 0:
                                selected_entity = clicked_tile.pop()   # remove top entity
                                update_screen(screen, board, main_viewport_rect, palette_viewport_rect, redraw_board=True, selected_entity=selected_entity, cursor_position=event.pos)

                        else:
                            # deselect the entity and redraw
                            clicked_tile.append(selected_entity)
                            discard_selected_item()

                    # handle palette viewport clicks
                    elif palette_viewport_rect.collidepoint(event.pos):
                        if selected_entity:
                            selected_entity = None
                            update_screen(screen, board, main_viewport_rect, palette_viewport_rect)
                        else:
                            x_tiles, y_tiles = pixels_to_tiles_palette(*event.pos, palette_viewport_rect, PALETTE_WIDTH, PALETTE_HEIGHT)
                            choice = PALETTE_LAYOUT[y_tiles][x_tiles]
                            selected_entity = choice
                            update_screen(screen, board, main_viewport_rect, palette_viewport_rect, redraw_board=True, selected_entity=selected_entity, cursor_position=event.pos)
                    
                    # handle background clicks (i.e. no viewports)
                    else:
                        discard_selected_item()

                elif event.button == 3:
                    discard_selected_item()
            
            elif event.type == pygame.MOUSEMOTION:
                if selected_entity:
                    if root_viewport_rect.collidepoint(event.pos):
                        update_screen(screen, board, main_viewport_rect, palette_viewport_rect, redraw_board=False, selected_entity=selected_entity, cursor_position=event.pos)

            elif event.type == pygame.KEYDOWN:
                key_mods = pygame.key.get_mods()

                # handle board size changes
                board_size_changed = False
                decreasing = key_mods & pygame.KMOD_SHIFT
                increasing = not decreasing
                # # format (x, y, delta)
                # size_delta = [0, 0, 0]  # one of (0,0,0), (-1,0,1),  (1,0,1),  (0,-1,1),  (0,1,1),
                #                         #                 (-1,0,-1), (1,0,-1), (0,-1,-1), (0,1,-1)
                if event.key == pygame.K_UP:
                    if increasing and board_height < BOARD_HEIGHT_RANGE[1]:
                        board.insert(0, [[] for _ in range(board_width)])
                        board_size_changed = True
                    elif decreasing and board_height > BOARD_HEIGHT_RANGE[0]:
                        board.pop(0)
                        board_size_changed = True
                elif event.key == pygame.K_DOWN:
                    if increasing and board_height < BOARD_HEIGHT_RANGE[1]:
                        board.append([[] for _ in range(board_width)])
                        board_size_changed = True
                    elif decreasing and board_height > BOARD_HEIGHT_RANGE[0]:
                        board.pop()
                        board_size_changed = True
                elif event.key == pygame.K_RIGHT:
                    if increasing and board_width < BOARD_WIDTH_RANGE[1]:
                        for row in board: row.append([])
                        board_size_changed = True
                    elif decreasing and board_height > BOARD_WIDTH_RANGE[0]:
                        for row in board: row.pop()
                        board_size_changed = True
                elif event.key == pygame.K_LEFT:
                    if increasing and board_width < BOARD_WIDTH_RANGE[1]:
                        for row in board: row.insert(0, [])
                        board_size_changed = True
                    elif decreasing and board_height > BOARD_WIDTH_RANGE[0]:
                        for row in board: row.pop()
                        board_size_changed = True
                
                if board_size_changed:
                    refresh_layout()
                
                # handle keyboard shortcuts
                if key_mods & pygame.KMOD_CTRL:
                    if event.key == pygame.K_o:
                        # Open
                        if board_save_state != board:
                            if not ask_yes_no("Level Editor", "You have unsaved work that will be overwitten by opening another level. Are you sure you want to continue?"):
                                continue
                        if res := ask_open_filename(**FILE_DIALOG_OPTIONS):
                            level_filename = res
                            board = read_level(level_filename)
                            board_save_state = board_copy(board)
                            refresh_layout()
                            refresh_caption()
                            print(f"opened {level_filename}")

                    elif event.key == pygame.K_s:
                        if key_mods & pygame.KMOD_SHIFT:
                            # Save as
                            if res := ask_save_as_filename(**FILE_DIALOG_OPTIONS):
                                level_filename = res
                                write_level(level_filename, board)
                                board_save_state = board_copy(board)
                                refresh_caption()
                                print(f"saved to {level_filename}")
                        else:
                            # Save
                            if level_filename is None:
                                if res := ask_save_as_filename(**FILE_DIALOG_OPTIONS):
                                    level_filename = res
                            if level_filename:
                                write_level(level_filename, board)
                                board_save_state = board_copy(board)
                                refresh_caption()
                                print(f"saved to {level_filename}")
                
                elif event.key == pygame.K_SPACE:
                    # spawn a new process running play_level (can only have one alive at a time)
                    if playtest_process is None or not playtest_process.is_alive():
                        playtest_process = Process(target=play_level, args=(Level(board_copy(board), logging=False),))
                        playtest_process.start()

            elif event.type == pygame.KEYUP:
                key_mods = pygame.key.get_mods()

USAGE_TEXT = """
    +------------- SHORTCUTS -------------+
    |  Open:       CTRL + O               |
    |  Save:       CTRL + S               |   
    |  Save as:    CTRL + SHIFT + S       |
    |  ---------------------------------  |     
    |  Size++:        ARROW-KEYS          |
    |  Size--:        SHIFT + ARROW-KEYS  |
    |  Repeat mode:   CAPS-LOCK           |
    |  Playtest:      SPACE               |
    +-------------------------------------+\
"""


if __name__ == "__main__":
    print(USAGE_TEXT)
    run_editor()
    # run_editor(levels[0])
