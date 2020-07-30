# Momo Is You
An ATLA-themed clone of the award-winning puzzle game Baba Is You

From the [Baba Is You](https://hempuli.com/baba/) home page:
> Baba Is You is a puzzle game where the rules you have to follow are present as physical objects in the game world. By manipulating the rules, you can change how the game works, repurpose things you find in the levels and cause surprising interactions!

Implementing the dynamic rule system presents a unique programming challenge. This implementation strives to be as clean and **extensible** as possible. As such, it includes an abstract treatment of the rules' grammar structures which provide an approachable environment for creating new rules. The clone is written in Python using the Pygame module.

The theme is based on the beloved television series *Avatar: The Last Airbender*, and features a number of characters from the show including Momo and Appa. Conveniently, many of the characters have four-letter names (Aang, Toph, Zuko, Iroh, Ozai, ...) which easily fit onto the game's tiles.

**Example Level:**
![test level screenshot](https://github.com/rschwa6308/Momo-Is-You/blob/master/screenshots/test_level_screenshot.png)

**Level Editor:**
![level editor screenshot](https://github.com/rschwa6308/Momo-Is-You/blob/master/screenshots/level_editor_screenshot.png)

### Current Features
 - 3 playable levels
 - dynamic window-resizing
 - undo/restart
 - a functioning level editor
 - numerous supported game mechanics
   - WIN
   - MOVE
   - STOP
   - PUSH
   - DEFEAT
   - SINK
   - HAS

### TODO
 - menu and level-select screens
 - more game mechanics
   - HOT/MELT
   - SHUT/OPEN
   - MOVE
   - MAKE
