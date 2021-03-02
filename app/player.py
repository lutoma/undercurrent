import gi
import sys

gi.require_version('Gst', '1.0')

from gi.repository import GLib, Gst # noqa


class Player:
	implicit_queue = []
	explicit_queue = []
	is_playing = False

	def __init__(self):
		Gst.init(None)
		self.playbin = Gst.ElementFactory.make('playbin', None)
		if not self.playbin:
			print('Could not initialize gstreamer playbin module', file=sys.stderr)
			sys.exit(1)

		bus = self.playbin.get_bus()
		bus.add_signal_watch()
		bus.connect('message', self.bus_call, None)

	def bus_call(self, bus, message, loop):
		t = message.type

		if t == Gst.MessageType.EOS:
			self.is_playing = False
			print('End of stream')
			self.playbin.set_state(Gst.State.READY)
		elif t == Gst.MessageType.STREAM_STATUS:
			print('Status change {}'.format(message.parse_stream_status()))
		elif t == Gst.MessageType.BUFFERING:
			progress = message.parse_buffering()
			print('Buffering {}%'.format(progress))
		elif t == Gst.MessageType.ERROR:
			err, debug = message.parse_error()
			print('Error: {}: {}\n'.format(err, debug), file=sys.stderr)

		return True

	def set_volume(self, vol):
		self.playbin.set_property('volume', vol)

	def queue(self, url):
		self.playbin.set_property('uri', url)

	def play(self):
		self.is_playing = True
		self.playbin.set_state(Gst.State.PLAYING)

	def pause(self):
		self.is_playing = False
		self.playbin.set_state(Gst.State.PAUSED)

	def stop(self):
		self.is_playing = False
		self.playbin.set_state(Gst.State.READY)

	def quit(self):
		self.is_playing = False
		self.playbin.set_state(Gst.State.NULL)

	def get_duration(self):
		success, duration = self.playbin.query_duration(Gst.Format.TIME)
		if not success:
			return 0

		return duration / Gst.SECOND

	def get_position(self):
		success, progress = self.playbin.query_position(Gst.Format.TIME)
		if not success:
			return 0

		return progress / Gst.SECOND

	def seek(self, seconds):
		self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
			seconds * Gst.SECOND)
