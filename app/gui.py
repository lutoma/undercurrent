import gi
import urllib

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, GLib, Gio, Gdk, GObject, Pango # noqa
from gi.repository.GdkPixbuf import Pixbuf # noqa


class ListBoxRowWithData(Gtk.ListBoxRow):
	def __init__(self, data, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.data = data


class GUIEventHandlers:
	def __init__(self, gui):
		self.gui = gui

	def on_main_destroy(self, *args):
		self.gui.player.quit()
		Gtk.main_quit()

	def on_main_menu_about_activate(self, widget):
		dialog = self.gui.builder.get_object('about_dialog')
		dialog.connect('delete-event', lambda w, e: dialog.hide() or True)
		dialog.show_all()

	def on_playlists_row_activated(self, widget, row):
		self.gui.switch_to_playlist(row.data)

	def on_tracklist_row_activated(self, widget, row):
		track = row.data

		song_label = self.gui.builder.get_object('status_song')
		song_label.set_label(track.name)

		artist_label = self.gui.builder.get_object('status_artist')
		artist_label.set_label(track.artist.name)

		self.gui.load_image_from_url('status_album_image', track.album.picture(width=80, height=80))

		url = self.gui.tidal.get_media_url(track.id)
		self.gui.player.stop()
		self.gui.player.queue(url)
		self.gui.player.play()

	def on_status_volume_value_changed(self, widget, val):
		self.gui.player.set_volume(val)

	def on_status_progress_change(self, widget, event):
		self.gui.player.seek(widget.get_value())

	def on_tracklist_filter_changed(self, widget):
		self.gui.tracklist_filter = widget.get_text()
		self.gui.tracklist.invalidate_filter()

	def on_play_button_clicked(self, *args):
		if self.gui.player.is_playing:
			self.gui.player.pause()
		else:
			self.gui.player.play()


class PlayerGUI:
	active_playlist = None
	play_state = False
	tracklist_filter = None

	def __init__(self, player, tidal):
		self.player = player
		self.tidal = tidal

		self.event_handlers = GUIEventHandlers(self)

		GLib.set_application_name('Undercurrent')
		self.builder = Gtk.Builder()
		self.builder.add_from_file('undercurrent.glade')
		self.builder.connect_signals(self.event_handlers)

		css_provider = Gtk.CssProvider()
		css_provider.load_from_path('undercurrent.css')
		context = Gtk.StyleContext()
		screen = Gdk.Screen.get_default()
		context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

		self.window = self.builder.get_object('main_window')
		self.window.set_wmclass("Undercurrent", "Undercurrent")
		self.window.show_all()

		self.tracklist = self.builder.get_object('tracklist')
		self.tracklist.set_filter_func(self.tracklist_filter_func)

		self.status_progress = self.builder.get_object('status_progress')
		self.playlists = self.builder.get_object('playlists')
		self.playback_timer = self.builder.get_object('status_playback_timer')
		self.play_button_image = self.builder.get_object('play_button_image')

		GObject.timeout_add_seconds(1, self.refresh_player_state)

	def run(self):
		Gtk.main()

	def load_image_from_url(self, target, url):
		image = self.builder.get_object(target)
		if not image:
			return

		response = urllib.request.urlopen(url)
		input_stream = Gio.MemoryInputStream.new_from_data(response.read(), None)
		pixbuf = Pixbuf.new_from_stream(input_stream, None)
		image.set_from_pixbuf(pixbuf)

	def tracklist_filter_func(self, row):
		if not self.tracklist_filter:
			return True

		search = self.tracklist_filter.lower()
		track = row.data
		return any({
			search in track.name.lower(),
			search in track.album.name.lower(),
			search in track.artist.name.lower(),
		})

	def refresh_player_state(self):
		# FIXME Should probably track playing state and only update icon on state change
		if not self.player.is_playing:
			self.play_button_image.set_from_stock('gtk-media-play', Gtk.IconSize.LARGE_TOOLBAR)
			self.status_progress.set_value(0)
			self.playback_timer.set_label('0:00 / 0:00')
			return True

		self.play_button_image.set_from_stock('gtk-media-pause', Gtk.IconSize.LARGE_TOOLBAR)

		duration = self.player.get_duration()
		position = self.player.get_position()

		self.status_progress.set_range(0, duration)
		self.status_progress.set_value(position)

		self.playback_timer.set_label('{}:{:02d} / {}:{:02d}'.format(
			int(position / 60),
			int(position % 60),
			int(duration / 60),
			int(duration % 60)
		))

		# self.status_progress.set_fill_level(67.0)
		return True

	def add_track(self, track):
		row = ListBoxRowWithData(data=track)
		box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		row.add(box)

		track_name = Gtk.Label()
		escaped_name = GLib.markup_escape_text(track.name)
		track_name.set_markup(f'<b><big>{escaped_name}</big></b>')
		track_name.set_xalign(0.0)
		box.add(track_name)

		artist_name = Gtk.Label(label=track.artist.name)
		artist_name.set_xalign(0.0)
		box.add(artist_name)

		self.tracklist.add(row)
		self.tracklist.show_all()

	def add_playlist(self, playlist):
		row = ListBoxRowWithData(data=playlist)
		label = Gtk.Label(label=playlist.name)
		label.set_xalign(0.0)
		label.set_ellipsize(Pango.EllipsizeMode.END)
		row.add(label)

		playlists = self.builder.get_object('playlists')
		playlists.add(row)
		playlists.show_all()

	def switch_to_playlist(self, playlist):
		self.active_playlist = playlist

		# Scroll up playlist viewport
		self.builder.get_object('playlist_scrolled_window').get_vadjustment().set_value(0)

		# Clear tracklist filter
		self.builder.get_object('tracklist_filter').set_text('')

		playlist_name = self.builder.get_object('playlist_name')
		escaped_name = GLib.markup_escape_text(playlist.name)
		playlist_name.set_markup(f'<span font="30" font_weight="ultrabold">{escaped_name}</span>')

		header_bar = self.builder.get_object('header_bar')
		header_bar.set_subtitle(playlist.name)

		self.load_image_from_url('playlist_image', playlist.picture(width=160, height=160))

		for row in self.tracklist.get_children():
			row.destroy()

		tracks = self.tidal.get_playlist_tracks(playlist.id)
		for track in tracks:
			self.add_track(track)
