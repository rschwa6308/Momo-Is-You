# Loading Assets from disc

import pygame
import os

ASSETS_DIRECTORY_NAME = "assets"
ASSETS_DIRECTORY_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), ASSETS_DIRECTORY_NAME)

# --- Load All Image Assets --- #
src_image_filenames = ["momo_128.png", "wall_128.png", "rock_128.png", "flag_128.png"]
src_images = {}
for filename in src_image_filenames:
    id = "_".join(filename.split("_")[:-1]) + "_src"
    path = os.path.join(ASSETS_DIRECTORY_PATH, filename)
    image = pygame.image.load(path)
    src_images.update({id: image})
