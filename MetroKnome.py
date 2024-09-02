import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import pygame
import time
import threading
from pathlib import Path
from typing import List, Tuple

DEFAULT_BPM = 120
DEFAULT_VOLUME = 0.5
DEFAULT_TIME_SIGNATURE = (4, 4)

class MetronomeWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="MetroKnome")
        self.set_border_width(10)

        try:
            pygame.mixer.init()
            script_dir = Path(__file__).parent.resolve()
            self.normal_click = pygame.mixer.Sound(script_dir / "tock.wav")
            self.accent_click = pygame.mixer.Sound(script_dir / "tick.wav")
        except pygame.error as e:
            self.show_error_dialog(f"Error initializing audio: {e}")
            return

        self.bpm: int = DEFAULT_BPM
        self.volume: float = DEFAULT_VOLUME
        self.is_playing: bool = False
        self.beat_count: int = 0
        self.time_signature: Tuple[int, int] = DEFAULT_TIME_SIGNATURE
        self.lock = threading.Lock()

        self.setup_ui()

    def setup_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_homogeneous(False)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        self.add(main_box)

        # BPM
        bpm_box = Gtk.Box(spacing=5)
        bpm_label = Gtk.Label(label="BPM:")
        self.bpm_entry = Gtk.Entry()
        self.bpm_entry.set_text(str(self.bpm))
        self.bpm_entry.set_width_chars(5)
        self.bpm_entry.connect("activate", self.on_bpm_changed)
        bpm_button = Gtk.Button(label="Set BPM")
        bpm_button.connect("clicked", self.on_bpm_changed)
        bpm_box.pack_start(bpm_label, False, False, 0)
        bpm_box.pack_start(self.bpm_entry, True, True, 0)
        bpm_box.pack_start(bpm_button, False, False, 0)
        main_box.pack_start(bpm_box, False, False, 0)

        # Volume
        volume_box = Gtk.Box(spacing=5)
        volume_label = Gtk.Label(label="Volume:")
        self.volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.1)
        self.volume_scale.set_value(self.volume)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        volume_box.pack_start(volume_label, False, False, 0)
        volume_box.pack_start(self.volume_scale, True, True, 0)
        main_box.pack_start(volume_box, False, False, 0)

        # Time Signature
        time_sig_box = Gtk.Box(spacing=5)
        time_sig_label = Gtk.Label(label="Time Signature:")
        self.time_sig_entry = Gtk.Entry()
        self.time_sig_entry.set_text(f"{self.time_signature[0]}/{self.time_signature[1]}")
        self.time_sig_entry.set_width_chars(5)
        self.time_sig_entry.connect("activate", self.on_time_signature_changed)
        time_sig_button = Gtk.Button(label="Set")
        time_sig_button.connect("clicked", self.on_time_signature_changed)
        time_sig_box.pack_start(time_sig_label, False, False, 0)
        time_sig_box.pack_start(self.time_sig_entry, True, True, 0)
        time_sig_box.pack_start(time_sig_button, False, False, 0)
        main_box.pack_start(time_sig_box, False, False, 0)

        # Start/Stop Button
        self.start_stop_button = Gtk.Button(label="Start")
        self.start_stop_button.connect("clicked", self.on_start_stop_clicked)
        main_box.pack_start(self.start_stop_button, False, False, 0)

        # Beat Indicator
        self.beat_indicator = Gtk.Label()
        self.beat_indicator.set_markup('<span size="xx-large">●</span>')
        main_box.pack_start(self.beat_indicator, False, False, 0)

    def on_bpm_changed(self, widget):
        try:
            new_bpm = int(self.bpm_entry.get_text())
            if new_bpm <= 0:
                raise ValueError
            self.bpm = new_bpm
            if self.is_playing:
                self.stop_metronome()
                self.start_metronome()
        except ValueError:
            self.show_error_dialog("Invalid BPM value. Please enter a positive integer.")

    def on_volume_changed(self, widget):
        self.volume = self.volume_scale.get_value()
        self.normal_click.set_volume(self.volume)
        self.accent_click.set_volume(self.volume)

    def on_time_signature_changed(self, widget):
        try:
            beats, unit = map(int, self.time_sig_entry.get_text().split('/'))
            if beats <= 0 or unit <= 0:
                raise ValueError
            self.time_signature = (beats, unit)
        except ValueError:
            self.show_error_dialog("Invalid time signature. Please use the format 'beats/unit' (e.g., 4/4).")

    def on_start_stop_clicked(self, widget):
        if self.is_playing:
            self.stop_metronome()
        else:
            self.start_metronome()

    def start_metronome(self):
        with self.lock:
            self.is_playing = True
        self.start_stop_button.set_label("Stop")
        self.metronome_thread = threading.Thread(target=self.metronome_loop)
        self.metronome_thread.start()

    def stop_metronome(self):
        with self.lock:
            self.is_playing = False
        self.start_stop_button.set_label("Start")
        self.beat_indicator.set_markup('<span size="xx-large">●</span>')

    def metronome_loop(self):
        next_beat_time = time.time()
        while True:
            with self.lock:
                if not self.is_playing:
                    break
                interval = 60 / self.bpm
                current_beat = self.beat_count % self.time_signature[0]

            current_time = time.time()
            if current_time >= next_beat_time:
                try:
                    if current_beat == 0:
                        self.accent_click.play()
                        GLib.idle_add(self.update_beat_indicator, True)
                    else:
                        self.normal_click.play()
                        GLib.idle_add(self.update_beat_indicator, False)
                except pygame.error as e:
                    GLib.idle_add(self.show_error_dialog, f"Error playing sound: {e}")
                    break

                with self.lock:
                    self.beat_count += 1
                next_beat_time += interval
            time.sleep(0.001)  # Short sleep to prevent busy-waiting

    def update_beat_indicator(self, is_accent: bool) -> bool:
        color = "#4CAF50" if is_accent else "#2196F3"
        self.beat_indicator.set_markup(f'<span size="xx-large" foreground="{color}">●</span>')
        return False

    def show_error_dialog(self, message: str):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def cleanup(self):
        pygame.quit()

def main():
    win = MetronomeWindow()
    win.connect("destroy", lambda x: Gtk.main_quit())
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()