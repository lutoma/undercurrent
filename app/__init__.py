import tidalapi
import configparser
from pathlib import Path
import os

from .player import Player
from .gui import PlayerGUI


def run():
	xdg_config_home = os.getenv("XDG_CONFIG_HOME")
	if xdg_config_home:
		config_dir = Path(xdg_config_home)
	else:
		config_dir = Path.home() / '.config'

	config_file = config_dir / 'undercurrent.conf'

	config = configparser.ConfigParser()
	config.read(config_file)

	if not config.has_section('tidal_auth'):
		print('Missing tidal auth')
		exit()

	tidal_config = tidalapi.Config(quality=tidalapi.Quality.lossless)
	tidal = tidalapi.Session(config=tidal_config)
	tidal.login(config.get('tidal_auth', 'user'), config.get('tidal_auth', 'pass'))

	player = Player()
	gui = PlayerGUI(player, tidal)

	playlists = tidal.user.playlists()
	for pl in playlists:
		gui.add_playlist(pl)

	gui.run()
