tmxOptimizer
============

Tool for optimizing tilemap (tmx format)

Making a tilemap is never an easy work, event thought there’re a lot of UI tilemap editor tools. 
One of them is Tile Map Editor tool http://www.mapeditor.org/. 
They help us create a map, but we have to prepare tilesets by ourselves. 
That’s a 10x harder work to create  good enough tilesets (no redundant tile)  for a big map. 
For  Tile Map Editor tool, that’s a nightmare if you try to optimize tileset by yourself
(reducing/increasing size of tileset image, removing/replacing tile).

This tool gathers information in your tilemap, removes unused tiles, 
re-organizes tileset images to most optimized way, corrects tilemap data according to new tileset.

This tool also supports optimize multiple tileset files with *the same structure*:
+ same layers structure: layer index, layer type
+ same tileset structure: tileset files, tileset index

===
Requirement:
+ Python 2.7
+ PIL 1.1.7
+ minidom

===
Execute:

+ put optile.py & @optile_config.xml in the same place with tmx-files
+ open @optile_config.xml
  + Add/remove/edit input file, which share the same set of tileset
  + Add/remove/edit keep file, which is tileset file that not be cropped after optimizing
+ output will be placed in output folder.