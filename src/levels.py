# Level board starting states
# TODO: read these layouts from external files

import os

from entities import *

# Map from file key-strings to entities
# key-strings must be < 5 chars long and should be human-readable; asterisk indicates object
# key-strings not present in this dict will be mapped to empty space
KEYSTR_ENTITY_MAP = {
    "MOM*": Objects.MOMO,
    "WAL*": Objects.WALL,
    "ROC*": Objects.ROCK,
    "FLA*": Objects.FLAG,
    "WAT*": Objects.WATER,

    "MOMO": Nouns.MOMO,
    "WALL": Nouns.WALL,
    "ROCK": Nouns.ROCK,
    "FLAG": Nouns.FLAG,
    "WATE": Nouns.WATER,

    "IS": Verbs.IS,
    "HAS": Verbs.HAS,

    "YOU": Adjectives.YOU,
    "WIN": Adjectives.WIN,
    "STOP": Adjectives.STOP,
    "PUSH": Adjectives.PUSH,
    "DEFE": Adjectives.DEFEAT,
    "SINK": Adjectives.SINK,
}

# Reversed KEYSTR_ENTITY_MAP
ENTITY_KEYSTR_MAP = {v: k for k, v in KEYSTR_ENTITY_MAP.items()}


TILE_DELIMITER = "|"
KEYSTR_DELIMITER = ","

EMPTY_TILE_STR = "_"


LEVELS_DIR = os.path.join(os.path.dirname(__file__), "levels")
SAVED_LEVELS_DIR = os.path.join(LEVELS_DIR, "saved")


# Read a level-start from a given filename
def read_level_start(filename):
    level_start = []
    abs_filename = os.path.join(LEVELS_DIR, filename)

    if not os.path.isfile(abs_filename):
        raise FileNotFoundError(f"Given filename '{filename}' does not exist.")

    with open(abs_filename) as file:
        for line in file.readlines():
            row = []
            for tile in line.rstrip().split(TILE_DELIMITER):
                if tile == EMPTY_TILE_STR:
                    row.append([])
                else:
                    keystrs = tile.split(KEYSTR_DELIMITER)
                    row.append([KEYSTR_ENTITY_MAP[keystr] for keystr in keystrs])
            level_start.append(row)

    return level_start



# Write a given level-start to a given filename
def write_level_start(filename, board):
    if not filename.endswith(".lvl"):
        raise ValueError(f"Given filename '{filename}' is invalid. Filenames must end with '.lvl'.")

    def tile_to_str(tile):
        if not tile:
            return EMPTY_TILE_STR
        else:
            return KEYSTR_DELIMITER.join(ENTITY_KEYSTR_MAP[e] for e in tile)

    row_strs = [
        TILE_DELIMITER.join(tile_to_str(tile) for tile in row)
        for row in board
    ]

    out = "\n".join(row_strs)

    abs_filename = os.path.join(SAVED_LEVELS_DIR, filename)
    with open(abs_filename, mode='w') as f:
        f.write(out)



# --- Load All Levels --- #
level_names = ["level_1"]
level_starts = [
    read_level_start(f"{level_name}.lvl")
    for level_name in level_names
]

write_level_start('blah.lvl', level_starts[0])


# M = Objects.MOMO
# W = Objects.WALL
# R = Objects.ROCK
# F = Objects.FLAG
#
# IS = Verbs.IS
#
# test_level_1_start = [
#     [[Nouns.MOMO], [IS], [Adjectives.YOU], [], [], [W], [], [], [], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[], [], [M], [], [], [R], [], [], [F], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[Nouns.WALL], [Nouns.ROCK], [], [], [], [W], [], [], [], [], []],
#     [[IS], [IS], [], [], [], [W], [], [], [], [], []],
#     [[Adjectives.STOP], [Adjectives.PUSH], [], [], [], [W], [], [], [Nouns.FLAG], [IS], [Adjectives.WIN]]
# ]
#
# test_level_2_start = [
#     [[Nouns.MOMO], [IS], [Adjectives.YOU], [], [], [W], [], [], [], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[], [], [M], [], [], [W], [], [], [F], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[], [Nouns.WALL], [], [], [], [W], [], [], [], [], []],
#     [[], [IS], [], [], [], [W], [], [], [], [], []],
#     [[], [Adjectives.STOP], [], [], [], [W], [], [], [Nouns.FLAG], [IS], [Adjectives.WIN]]
# ]
#
# test_level_3_start = [[[] for x in range(20)] for y in range(15)]
# test_level_3_start[0][0:3] = [[Nouns.MOMO], [IS], [Adjectives.YOU]]
# test_level_3_start[1][0:3] = [[Nouns.WATER], [IS], [Adjectives.SINK]]
# test_level_3_start[-1][0:3] = [[Nouns.ROCK], [IS], [Adjectives.PUSH]]
# test_level_3_start[-2][0:3] = [[Nouns.FLAG], [IS], [Adjectives.WIN]]
# test_level_3_start[5][4] = [Objects.MOMO]
# test_level_3_start[8][4] = [Objects.ROCK]
# for row in test_level_3_start: row[12] = [Objects.WATER]
# test_level_3_start[7][18] = [Objects.FLAG]
#
# test_level_4_start = [
#     [[Nouns.MOMO], [IS], [Adjectives.YOU], [], [], [W], [], [], [], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[], [], [IS], [], [], [W], [], [], [], [], []],
#     [[], [], [], [], [], [W], [], [], [], [], []],
#     [[], [], [M], [], [], [W], [], [], [F], [], []],
#     [[], [], [], [Nouns.MOMO], [], [W], [], [], [], [], []],
#     [[Nouns.WALL], [], [], [], [], [W], [], [], [], [], []],
#     [[IS], [], [], [], [], [W], [], [], [], [], []],
#     [[Adjectives.STOP], [], [], [], [], [W], [], [], [Nouns.FLAG], [IS], [Adjectives.WIN]]
# ]
#
# level_starts = [test_level_1_start, test_level_2_start, test_level_3_start, test_level_4_start]
