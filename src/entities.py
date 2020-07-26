from enum import Enum, auto


# Abstract class encompassing all entities which can be in a level's board
class Entities:
    pass


class Objects(Entities, Enum):
    MOMO = auto()
    WALL = auto()
    ROCK = auto()
    FLAG = auto()
    WATER = auto()


# Abstract class encompassing all text elements
class Text(Entities):
    pass


# Abstract class encompassing all text elements that can function as subject complements
class Complements(Text):
    pass


class Nouns(Complements, Enum):
    MOMO = auto()
    WALL = auto()
    ROCK = auto()
    FLAG = auto()
    WATER = auto()


class Adjectives(Complements, Enum):
    YOU = auto()
    WIN = auto()
    STOP = auto()
    PUSH = auto()
    DEFEAT = auto()
    SINK = auto()


class Verbs(Text, Enum):
    IS = auto()
    HAS = auto()


# Map from all Nouns to all corresponding Objects
noun_object_map = {
    Nouns.MOMO: Objects.MOMO,
    Nouns.WALL: Objects.WALL,
    Nouns.ROCK: Objects.ROCK,
    Nouns.FLAG: Objects.FLAG,
    Nouns.WATER: Objects.WATER
}
