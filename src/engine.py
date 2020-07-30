# Game Engine

from entities import *


# --- Primary Engine Class; handles all game logic --- #
class Level:
    # input keys TODO replace with internal enum?
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    WAIT = "wait"
    UNDO = "undo"
    RESTART = "restart"

    # valid rule patterns
    rule_patterns = [
        [Nouns, Verbs.IS, Complements],
        [Nouns, Verbs.HAS, Nouns]
    ]

    def __init__(self, board, logging=True):
        if len(board) == 0 or len(board[0]) == 0:
            raise ValueError("Invalid board shape; board cannot be empty.")

        if any(len(row) != len(board[0]) for row in board):
            raise ValueError("Invalid board shape; board must be rectangular.")

        if any(any(any(not isinstance(value, Entities) for value in tile) for tile in row) for row in board):
            raise ValueError("Invalid board contents; board can only contain Entities.")

        self.board = board
        self.height = len(board)
        self.width = len(board[0])

        self.logging = logging     # logging enabled by default

        self.rules_dict = {}
        self.implicit_rules = [(Text, Verbs.IS, Adjectives.PUSH)]
        self.parse_rules_from_board()

        self.board_history = []

        self.has_won = False

    # Primary API method; handles all processing for a given input key
    # Returns true iff board state is changed
    def process_input(self, key):
        if self.logging: print("\nprocess_input(%s)" % key)

        board_state_changed = False

        if key == Level.UNDO:
            if len(self.board_history) > 0:
                self.board = self.board_history.pop()
                self.parse_rules_from_board()
        elif key == Level.RESTART:
            if len(self.board_history) > 0:
                self.board = self.board_history[0]
                self.board_history.clear()
                self.parse_rules_from_board()
        else:
            self.board_history.append(board_copy(self.board))  # add copy of current board state to history

            if key in (Level.UP, Level.DOWN, Level.LEFT, Level.RIGHT):
                if self.handle_motion(key):     # always handle motion
                    board_state_changed = True

            if self.apply_proactive_rules():    # always apply proactive rules
                board_state_changed = True

            if board_state_changed:             # only re-parse when board state has been changed
                self.parse_rules_from_board()

            if self.apply_reactive_rules():     # always apply reactive rules
                board_state_changed = True
        
        return board_state_changed

    def get_tile_at(self, x, y):
        return self.board[y][x]

    # Handles all level motion (assumes that self.rules_dict is constant); returns true iff board state is changed
    def handle_motion(self, direction_key):
        if self.logging: print("\thandle_motion(%s)" % direction_key)

        yous = []
        for y in range(self.height):
            for x in range(self.width):
                for entity in self.get_tile_at(x, y):
                    if self.get_ruling(entity, Verbs.IS, Adjectives.YOU):
                        yous.append((entity, (x, y)))

        if len(yous) == 0:
            if self.logging: print("\t\tyou are nothing!!!")
            return False

        displacement_vector = {
            Level.UP: (0, -1),
            Level.DOWN: (0, 1),
            Level.LEFT: (-1, 0),
            Level.RIGHT: (1, 0)
        }[direction_key]

        board_state_changed = False
        for you in yous:
            entity, starting_coords = you
            target_coords = vector_sum(starting_coords, displacement_vector)

            # scan in direction of displacement vector for level bounds, STOP Objects, and PUSH Objects
            moves = [(entity, starting_coords, target_coords)]
            scanning_coords = target_coords
            stopped = False
            while True:
                if not self.is_walkable(scanning_coords):
                    stopped = True
                    break

                scanning_tile = self.get_tile_at(*scanning_coords)
                contains_pushable = False
                for e in scanning_tile:
                    if self.get_ruling(e, Verbs.IS, Adjectives.PUSH):
                        moves.append((e, scanning_coords, vector_sum(scanning_coords, displacement_vector)))
                        contains_pushable = True

                if not contains_pushable:  # empty tile encountered
                    break

                scanning_coords = vector_sum(scanning_coords, displacement_vector)

            # move entity
            if not stopped:
                board_state_changed = True
                for move in moves:
                    self.move_entity(*move)

        return board_state_changed

    def is_in_bounds(self, tile_coords):
        return 0 <= tile_coords[0] < self.width and 0 <= tile_coords[1] < self.height

    # Returns true iff the given coords are in bounds and the corresponding tile does not contain a STOP Object
    def is_walkable(self, tile_coords):
        if not self.is_in_bounds(tile_coords):
            return False

        tile = self.get_tile_at(*tile_coords)
        return not any(self.get_ruling(e, Verbs.IS, Adjectives.STOP) for e in tile)

    def move_entity(self, entity, starting_coords, ending_coords):
        self.get_tile_at(*starting_coords).remove(entity)
        self.get_tile_at(*ending_coords).append(entity)

    # Adds a given rule to self.rules_dict
    # (object, verb, complement)
    def add_rule(self, subject, predicate, complement):
        if subject not in self.rules_dict.keys():
            self.rules_dict[subject] = {}
        object_rules = self.rules_dict[subject]

        if predicate not in object_rules.keys():
            object_rules[predicate] = set()

        object_rules[predicate].add(complement)

    # Returns the set of complements currently associated with the given subject/predicate pair;
    # returns None if pair is not found
    def get_rule(self, subject, predicate):
        if isinstance(subject, Text):  # ignore text subtype
            subject = Text

        if subject not in self.rules_dict.keys():
            return None
        object_rules = self.rules_dict[subject]

        if predicate not in object_rules:
            return None

        return object_rules[predicate]

    # Returns true iff the given rule query is explicitly present in self.rules_dict
    def get_ruling(self, subject, predicate, complement):
        rule = self.get_rule(subject, predicate)

        if rule is None:
            return False

        return complement in rule

    # Call add_rule() on all 'implicit' rules
    def add_implicit_rules(self):
        for rule in self.implicit_rules:
            self.add_rule(*rule)

    # Scans the board for valid text patterns and calls add_rule() on all matches
    # TODO: research how Baba handles case of overlapping text
    def parse_rules_from_board(self):
        if self.logging: print("\tparse_rules_from_board()")

        self.rules_dict.clear()
        self.add_implicit_rules()

        # horizontal scan
        for x in range(self.width - 2):
            for y in range(self.height):
                tiles = [self.get_tile_at(x + offset, y) for offset in range(3)]
                filtered_tiles = [list(filter(lambda e: isinstance(e, Text), tile)) for tile in tiles]
                if all(len(tile) > 0 for tile in filtered_tiles):
                    texts = [tile[0] for tile in filtered_tiles]  # only examine first Text instance found
                    if any(matches_pattern(pattern, texts) for pattern in self.rule_patterns):
                        self.add_rule(get_object_from_noun(texts[0]), texts[1], texts[2])

        # vertical scan
        for x in range(self.width):
            for y in range(self.height - 2):
                tiles = [self.get_tile_at(x, y + offset) for offset in range(3)]
                filtered_tiles = [list(filter(lambda e: isinstance(e, Text), tile)) for tile in tiles]
                if all(len(tile) > 0 for tile in filtered_tiles):
                    texts = [tile[0] for tile in filtered_tiles]  # only examine first Text instance found
                    if any(matches_pattern(pattern, texts) for pattern in self.rule_patterns):
                        self.add_rule(get_object_from_noun(texts[0]), texts[1], texts[2])

        if self.logging: print("\t\trules_dict:", self.rules_dict)

    # Applies all 'proactive' rules (i.e MOVE, MAKE(?)); returns true iff board state is changed
    def apply_proactive_rules(self):
        if self.logging: print("\tapply_proactive_rules()")
        return False  # TODO

    # Applies all 'reactive' rules (i.e. WIN, SINK, DEFEAT, Noun IS Noun); returns true iff board state is changed
    def apply_reactive_rules(self):
        if self.logging: print("\tapply_reactive_rules()")

        board_state_changed = False
        for x in range(self.width):
            for y in range(self.height):
                tile = self.get_tile_at(x, y)
                for entity in tile[:]:  # iterate over copy of tile to avoid concurrent modification issues

                    # check for YOU intersections (WIN is checked last)
                    if self.get_ruling(entity, Verbs.IS, Adjectives.YOU):
                        if any(self.get_ruling(e, Verbs.IS, Adjectives.DEFEAT) for e in tile):  # YOU/DEFEAT
                            self.destroy_entity(entity, (x, y))
                            board_state_changed = True
                        if any(self.get_ruling(e, Verbs.IS, Adjectives.WIN) for e in tile):  # YOU/WIN
                            self.has_won = True

                    # check for SINK intersections
                    if self.get_ruling(entity, Verbs.IS, Adjectives.SINK):
                        if len(tile) > 1:
                            for e in tile[:]:
                                self.destroy_entity(e, (x, y))
                            board_state_changed = True

                    # check for Noun IS Noun
                    complements = self.get_rule(entity, Verbs.IS)
                    if complements is not None:
                        objects = [get_object_from_noun(e) for e in complements if isinstance(e, Nouns)]
                        if len(objects) > 0:
                            tile.remove(entity)
                            tile += objects

        return board_state_changed

    # destroys one entity at given coords and spawns all HAS entities
    def destroy_entity(self, entity, tile_coords):
        tile = self.get_tile_at(*tile_coords)
        tile.remove(entity)

        has = self.get_rule(entity, Verbs.HAS)
        if has is not None:
            for spawn_entity in has:
                tile.append(spawn_entity)


# --- Helper Functions --- #

# Returns True iff the given entity list matches the given pattern
def matches_pattern(pattern, entities):
    return all(entity == target or (isinstance(target, type) and isinstance(entity, target)) for target, entity in
               zip(pattern, entities))


# Returns the object corresponding to the given noun
def get_object_from_noun(noun):
    return noun_object_map[noun]


def vector_sum(vector_a, vector_b):
    return tuple(a + b for a, b in zip(vector_a, vector_b))


# Returns a deep copy of the given board
def board_copy(board):
    return [[tile[:] for tile in row] for row in board]


def pprint(board):
    for row in board:
        print(" ".join(str(tile) for tile in row))
