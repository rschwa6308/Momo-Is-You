# --- UI Helpers used by both main and level_editor --- #

from functools import lru_cache
import pygame

from entities import *
from assets import src_images

# Maps entities to the resources required for drawing
entity_map = {
    Objects.MOMO: {
        "color": None,
        "src_image_id": "momo_src",
        "draw_precedence": 2
    },
    Objects.WALL: {
        "color": None,
        "src_image_id": "wall_src",
        "draw_precedence": 0
    },
    Objects.ROCK: {
        "color": None,
        "src_image_id": "rock_src",
        "draw_precedence": 1
    },
    Objects.FLAG: {
        "color": None,
        "src_image_id": "flag_src",
        "draw_precedence": 1
    },
    Objects.WATER: {
        "color": (0, 0, 255),  # TEMPORARY
        "src_image_id": None,
        "draw_precedence": 1
    },

    Nouns.MOMO: {
        "color": None,
        "src_image_id": None,
        "text_str": "MOMO",
        "text_color": (127, 0, 0),
        "draw_precedence": 2
    },
    Nouns.WALL: {
        "color": None,
        "src_image_id": None,
        "text_str": "WALL",
        "text_color": (127, 127, 0),
        "draw_precedence": 2
    },
    Nouns.ROCK: {
        "color": None,
        "src_image_id": None,
        "text_str": "ROCK",
        "text_color": (180, 127, 127),
        "draw_precedence": 2
    },
    Nouns.FLAG: {
        "color": None,
        "src_image_id": None,
        "text_str": "FLAG",
        "text_color": (127, 127, 127),
        "draw_precedence": 2
    },
    Nouns.WATER: {
        "color": None,
        "src_image_id": None,
        "text_str": "WATER",
        "text_color": (0, 0, 127),
        "draw_precedence": 2
    },

    Verbs.IS: {
        "color": None,
        "src_image_id": None,
        "text_str": "IS",
        "text_color": (255, 255, 255),
        "draw_precedence": 2
    },

    Adjectives.YOU: {
        "color": None,
        "src_image_id": None,
        "text_str": "YOU",
        "text_color": (255, 0, 255),
        "draw_precedence": 2
    },
    Adjectives.WIN: {
        "color": None,
        "src_image_id": None,
        "text_str": "WIN",
        "text_color": (127, 0, 255),
        "draw_precedence": 2
    },
    Adjectives.STOP: {
        "color": None,
        "src_image_id": None,
        "text_str": "STOP",
        "text_color": (127, 0, 127),
        "draw_precedence": 2
    },
    Adjectives.PUSH: {
        "color": None,
        "src_image_id": None,
        "text_str": "PUSH",
        "text_color": (63, 63, 127),
        "draw_precedence": 2
    },
    Adjectives.DEFEAT: {
        "color": None,
        "src_image_id": None,
        "text_str": "DEFEAT",
        "text_color": (63, 0, 0),
        "draw_precedence": 2
    },
    Adjectives.SINK: {
        "color": None,
        "src_image_id": None,
        "text_str": "SINK",
        "text_color": (63, 53, 0),
        "draw_precedence": 2
    }
}


# Scales given surface to given size and returns results (expensive, results should be cached)
def get_scaled_image(surface, size):
    return pygame.transform.smoothscale(surface, (size, size))


# Binary search to find font size with correct height to fill tile with 2 chars vertically and 3 horizontally
@lru_cache(maxsize=20)  # for good measure
def get_font(name, tile_size_px):
    pygame.font.init()

    size_lower_bound = 8
    size_upper_bound = 200

    target_size_px = int(tile_size_px * 0.58)

    font = None
    size = target_size_px  # initial guess
    while size_upper_bound - size_lower_bound > 1:
        font = pygame.font.SysFont(name, size, bold=True)
        text_size_px = max(font.size("M"))
        error = text_size_px - target_size_px
        # print(size, error, size_lower_bound, size_upper_bound)
        if error >= 0:
            size_upper_bound = size
        else:
            size_lower_bound = size
        size = (size_lower_bound + size_upper_bound) // 2

    return font


text_locations = {
    1: [(0.5, 0.5)],
    2: [(0.5, 0.25), (0.5, 0.75)],
    4: [(0.30, 0.27), (0.70, 0.27), (0.30, 0.73), (0.70, 0.73)]
}


# draws a square with rounded corners onto the given tile Surface
def draw_text_card_onto_tile(tile, color):
    tile_size_px = tile.get_width()
    corner_radius = tile_size_px // 6

    pygame.draw.rect(tile, color, pygame.Rect(0, corner_radius, tile_size_px, tile_size_px - corner_radius * 2))  # hor
    pygame.draw.rect(tile, color, pygame.Rect(corner_radius, 0, tile_size_px - corner_radius * 2, tile_size_px))  # vert

    pygame.draw.circle(tile, color, (corner_radius, corner_radius), corner_radius)
    pygame.draw.circle(tile, color, (tile_size_px - corner_radius, corner_radius), corner_radius)
    pygame.draw.circle(tile, color, (corner_radius, tile_size_px - corner_radius), corner_radius)
    pygame.draw.circle(tile, color, (tile_size_px - corner_radius, tile_size_px - corner_radius), corner_radius)


# Returns surface of size (tile_size_px, tile_size_px); cached for performance
@lru_cache(maxsize=len(entity_map) * 2)  # for good measure
def get_entity_image(entity, tile_size_px, bg_color):
    if entity_map[entity]["src_image_id"] is not None:
        # get scaled texture
        src_image = src_images[entity_map[entity]["src_image_id"]]
        return get_scaled_image(src_image, tile_size_px)
    else:
        # render text
        img = pygame.Surface((tile_size_px, tile_size_px), pygame.SRCALPHA)
        if isinstance(entity, Text):
            font = get_font("comicsansms", tile_size_px)
            text_str = entity_map[entity]["text_str"]
            if len(text_str) < 4:
                text_substrings = [text_str]  # 1 line
            elif len(text_str) == 4:
                text_substrings = [char for char in text_str[:4]]  # 2x2 grid
            else:
                text_substrings = [text_str[:3], text_str[3:]]

            if isinstance(entity, Adjectives):
                draw_text_card_onto_tile(img, entity_map[entity]["text_color"])
                text_color = bg_color
            else:
                text_color = entity_map[entity]["text_color"]

            text_images = [font.render(substr, True, text_color) for substr in text_substrings]
            locations = text_locations[len(text_images)]
            for text_img, loc in zip(text_images, locations):
                dest = (
                    tile_size_px * loc[0] - text_img.get_width() // 2,
                    tile_size_px * loc[1] - text_img.get_height() // 2
                )
                img.blit(text_img, dest)
        else:
            img.fill(entity_map[entity]["color"])
        return img


# Assumes given viewport surface has same exact aspect ratio as board (only draws squares)
def draw_board_onto_viewport(viewport, board, bg_color, grid_color=None):
    viewport.fill(bg_color)

    board_width, board_height = len(board[0]), len(board)

    tile_size_px = min(viewport.get_width() // board_width, viewport.get_height() // board_height)
    # print("tile_size_px:\t" + str(tile_size_px))

    for y in range(board_height):
        for x in range(board_width):
            tile_contents = board[y][x]
            tile_contents.sort(key=lambda e: entity_map[e]["draw_precedence"])
            for entity in tile_contents:
                img = get_entity_image(entity, tile_size_px, bg_color)
                loc_px = (tile_size_px * x, tile_size_px * y)
                viewport.blit(img, loc_px)

    if grid_color is not None:
        viewport_width, viewport_height = viewport.get_size()
        grid_surface = pygame.Surface((viewport_width, viewport_height), pygame.SRCALPHA)
        line_width = 1 + tile_size_px // 50

        for y in range(1, board_height):  # hor
            y_px = y * tile_size_px
            pygame.draw.line(grid_surface, grid_color, (0, y_px), (viewport_width, y_px), line_width)
        for x in range(1, board_width):  # vert
            x_px = x * tile_size_px
            pygame.draw.line(grid_surface, grid_color, (x_px, 0), (x_px, viewport_height), line_width)

        viewport.blit(grid_surface, (0, 0))
