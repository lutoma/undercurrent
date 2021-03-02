# undercurrent

A native Linux client/player for TIDAL. Written in Python using PyGObject with GTK and GStreamer.

## Features

Undercurent is in a "proof of concept" stage right now and pre-alpha. Very little works and the things that do work are likely buggy.

Working:

* Playback in "Normal/High/HiFi" qualities
* Playing from playlists

Does not work yet, but planned for future versions:

* Playing from own collection (favorited tracks/albums/artists)
* Search / browsing artists and albums
* MPRIS support for control from desktop environments/keyboard special keys
* Last.fm scrobbling

Does not work, and will probably not be added:

* Support for MQA ("Master" quality)
* Editing playlists

## Development setup

Make sure you have [poetry](https://python-poetry.org/) installed, then run

    poetry install

to install dependencies. You can then start the app using

    poetry run ./undercurrent

