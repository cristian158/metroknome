import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import pygame
import time
import threading
from pathlib import Path
from typing import List, Tuple, Optional # Added Optional

# --- Constants ---
DEFAULT_BPM = 120
DEFAULT_VOLUME = 0.5
DEFAULT_TIME_SIGNATURE = (4, 4)

BPM_UPPER_LIMIT = 777
TIME_SIGNATURE_BEATS_UPPER_LIMIT = 32
TIME_SIGNATURE_UNITS = [1, 2, 4, 8, 16, 32]
ACCENT_COLOR = "#4CAF50"
NORMAL_COLOR = "#2196F3"
DEFAULT_INDICATOR_MARKUP = '<span size="xx-large">●</span>'
THREAD_JOIN_TIMEOUT = 0.5 # Seconds

class MetronomeWindow(Gtk.Window):
    """
    A GTK window providing a visual metronome interface.

    Allows users to set BPM, volume, and time signature, start/stop the
    metronome, and provides visual feedback for each beat.
    """
    def __init__(self) -> None:
        """Initializes the MetronomeWindow, loads sounds, and sets up the UI."""
        Gtk.Window.__init__(self, title="MetroKnome")
        self.set_border_width(10)

        # --- Sound Loading ---
        try:
            script_dir = Path(__file__).parent.resolve()
            normal_click_path = script_dir / "tock.wav"
            accent_click_path = script_dir / "tick.wav"

            if not normal_click_path.exists():
                raise FileNotFoundError(f"Sound file not found: {normal_click_path}")
            if not accent_click_path.exists():
                raise FileNotFoundError(f"Sound file not found: {accent_click_path}")

            self.normal_click = pygame.mixer.Sound(normal_click_path)
            self.accent_click = pygame.mixer.Sound(accent_click_path)
        except FileNotFoundError as e:
            print(f"Error loading sound files: {e}")
            raise RuntimeError("Failed to load required sound files.") from e # Propagate error

        # --- State Variables ---
        self.bpm: int = DEFAULT_BPM
        self.volume: float = DEFAULT_VOLUME
        self.is_playing: bool = False
        self.beat_count: int = 0
        self.time_signature: Tuple[int, int] = DEFAULT_TIME_SIGNATURE

        # Thread safety lock
        self._lock = threading.Lock()
        self.metronome_thread: Optional[threading.Thread] = None # Initialize attribute

        self.setup_ui()

    def setup_ui(self) -> None:
        """Creates and arranges the GTK widgets for the metronome controls."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_homogeneous(False)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        self.add(main_box)

        self._setup_controls(main_box)

        # Start/Stop Button
        self.start_stop_button = Gtk.Button(label="Start")
        self.start_stop_button.connect("clicked", self.on_start_stop_clicked)
        main_box.pack_start(self.start_stop_button, False, False, 0)

        # Beat Indicator
        self.beat_indicator = Gtk.Label()
        self.beat_indicator.set_markup(DEFAULT_INDICATOR_MARKUP) # Use constant
        main_box.pack_start(self.beat_indicator, False, False, 0)

    def _setup_controls(self, parent_box: Gtk.Box) -> None:
        """Helper method to create and pack BPM, Volume, and Time Signature controls."""
        # --- BPM Controls ---
        bpm_box = Gtk.Box(spacing=5)
        bpm_label = Gtk.Label(label="BPM:")
        # Use SpinButton for BPM input
        bpm_adjustment = Gtk.Adjustment(value=self.bpm, lower=1, upper=BPM_UPPER_LIMIT, step_increment=1, page_increment=10, page_size=0)
        self.bpm_spin_button = Gtk.SpinButton(adjustment=bpm_adjustment, climb_rate=1, digits=0)
        self.bpm_spin_button.set_value(self.bpm)
        self.bpm_spin_button.connect("value-changed", self.on_bpm_changed) # Changed signal
        bpm_box.pack_start(bpm_label, False, False, 0)
        bpm_box.pack_start(self.bpm_spin_button, True, True, 0) # Removed Set button
        parent_box.pack_start(bpm_box, False, False, 0)

        # --- Volume Controls ---
        volume_box = Gtk.Box(spacing=5)
        volume_label = Gtk.Label(label="Volume:")
        self.volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.1)
        self.volume_scale.set_value(self.volume)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        volume_box.pack_start(volume_label, False, False, 0)
        volume_box.pack_start(self.volume_scale, True, True, 0)
        parent_box.pack_start(volume_box, False, False, 0)

        # --- Time Signature Controls ---
        time_sig_box = Gtk.Box(spacing=5)
        time_sig_label = Gtk.Label(label="Time Signature:")

        # Beats SpinButton
        beats_adjustment = Gtk.Adjustment(value=self.time_signature[0], lower=1, upper=TIME_SIGNATURE_BEATS_UPPER_LIMIT, step_increment=1, page_increment=1, page_size=0)
        self.beats_spin_button = Gtk.SpinButton(adjustment=beats_adjustment, climb_rate=1, digits=0)
        self.beats_spin_button.set_value(self.time_signature[0])
        self.beats_spin_button.connect("value-changed", self.on_time_signature_changed)

        # Separator Label
        separator_label = Gtk.Label(label="/")

        # Unit ComboBoxText
        self.unit_combo_box = Gtk.ComboBoxText()
        for unit in TIME_SIGNATURE_UNITS:
            self.unit_combo_box.append_text(str(unit))
        try:
            # Find the index of the default unit
            default_unit_index = TIME_SIGNATURE_UNITS.index(self.time_signature[1])
            self.unit_combo_box.set_active(default_unit_index)
        except ValueError:
            self.unit_combo_box.set_active(0) # Default to first if not found
        self.unit_combo_box.connect("changed", self.on_time_signature_changed)

        time_sig_box.pack_start(time_sig_label, False, False, 0)
        time_sig_box.pack_start(self.beats_spin_button, True, True, 0)
        time_sig_box.pack_start(separator_label, False, False, 5) # Add padding
        time_sig_box.pack_start(self.unit_combo_box, True, True, 0)
        # Removed Set button
        parent_box.pack_start(time_sig_box, False, False, 0)


    def on_bpm_changed(self, widget: Gtk.SpinButton) -> None:
        """Handles changes in the BPM spin button."""
        # Read value from SpinButton
        new_bpm = self.bpm_spin_button.get_value_as_int()
        # SpinButton already enforces range [1, BPM_UPPER_LIMIT]
        with self._lock:
            is_currently_playing = self.is_playing
            current_bpm = self.bpm

        if new_bpm != current_bpm:
            with self._lock:
                self.bpm = new_bpm
            if is_currently_playing:
                # Stop/start needs to handle its own locking
                self.stop_metronome()
                self.start_metronome()
        # No need for error dialog as SpinButton prevents invalid input

    def on_volume_changed(self, widget: Gtk.Scale) -> None:
        """Handles changes in the volume scale."""
        self.volume = self.volume_scale.get_value()
        self.normal_click.set_volume(self.volume)
        self.accent_click.set_volume(self.volume)

    def on_time_signature_changed(self, widget: Gtk.Widget) -> None:
        """
        Handles changes in the time signature controls (beats or unit).
        Restarts the metronome if it's playing.
        """
        # Read values from SpinButton and ComboBox
        new_beats = self.beats_spin_button.get_value_as_int()
        unit_text = self.unit_combo_box.get_active_text()

        if unit_text is None: # Should not happen if populated correctly
             return

        try:
            new_unit = int(unit_text)
        except (ValueError, TypeError):
             # Handle potential error if text is not an int (unlikely)
             self.show_error_dialog("Invalid time signature unit selected.")
             return

        new_time_signature = (new_beats, new_unit)

        # SpinButton and ComboBox enforce valid ranges/values
        with self._lock:
            is_currently_playing = self.is_playing
            current_time_signature = self.time_signature

        if new_time_signature != current_time_signature:
            with self._lock:
                self.time_signature = new_time_signature
            if is_currently_playing:
                # Stop/start needs to handle its own locking
                self.stop_metronome()
                self.start_metronome()
        # No need for extensive error checking/dialogs

    def on_start_stop_clicked(self, widget: Gtk.Button) -> None:
        """Toggles the metronome start/stop state."""
        # Read is_playing safely
        with self._lock:
             currently_playing = self.is_playing

        if currently_playing:
            self.stop_metronome()
        else:
            self.start_metronome()

    def start_metronome(self) -> None:
        """Starts the metronome beat thread."""
        with self._lock:
            # Prevent multiple metronome threads
            if self.metronome_thread is not None and self.metronome_thread.is_alive():
                return

            self.is_playing = True
            self.beat_count = 0
            # Schedule UI update on main thread
            GLib.idle_add(self.start_stop_button.set_label, "Stop")
            self.metronome_thread = threading.Thread(target=self.metronome_loop)
            self.metronome_thread.daemon = True  # Make thread daemon so it exits when main program exits
            self.metronome_thread.start()

    def stop_metronome(self) -> None:
        """Stops the metronome beat thread."""
        thread_to_join = None
        with self._lock:
            self.is_playing = False
            if self.metronome_thread is not None and self.metronome_thread.is_alive():
                 thread_to_join = self.metronome_thread # Get reference while holding lock

        # Schedule UI updates on main thread
        GLib.idle_add(self.start_stop_button.set_label, "Start")
        GLib.idle_add(self.beat_indicator.set_markup, DEFAULT_INDICATOR_MARKUP) # Use constant

        if thread_to_join:
           thread_to_join.join(THREAD_JOIN_TIMEOUT)  # Wait with timeout outside lock

    def metronome_loop(self) -> None:
        """
        The main loop for the metronome thread.

        Calculates beat timings, plays sounds, updates the UI indicator via
        GLib.idle_add, and handles stopping.
        """
        next_beat_time = time.time()
        while True:
            with self._lock:
                if not self.is_playing:
                    break # Exit loop if stopped
                current_bpm = self.bpm
                current_time_signature = self.time_signature
                beat_num = self.beat_count # Get current beat number

            # Calculations outside the lock
            # Calculate interval based on BPM (quarter notes) and time signature denominator
            # interval = (seconds_per_minute / bpm_quarter_notes) * (quarter_note_equivalent / beat_unit)
            # interval = (60.0 / current_bpm) * (4.0 / current_time_signature[1])
            interval = 240.0 / (current_bpm * current_time_signature[1])
            current_beat_in_measure = beat_num % current_time_signature[0]

            current_time = time.time()

            # --- Improved Timing ---
            time_to_next_beat = next_beat_time - current_time

            if time_to_next_beat <= 0: # If we're at or past the beat time
                try:
                    if current_beat_in_measure == 0:
                        self.accent_click.play()
                        GLib.idle_add(self.update_beat_indicator, True)
                    else:
                        self.normal_click.play()
                        GLib.idle_add(self.update_beat_indicator, False)
                except pygame.error as e:
                    # Schedule error dialog on main thread
                    GLib.idle_add(self.show_error_dialog, f"Error playing sound: {e}")
                    with self._lock: # Safely stop playing on error
                        self.is_playing = False
                    break # Exit loop on sound error

                with self._lock:
                    # Increment beat count only after playing the sound
                    self.beat_count += 1

                # Calculate next beat time based on the *scheduled* time, not current time
                # This prevents drift
                next_beat_time += interval

                # Recalculate sleep time in case interval is very short
                time_to_next_beat = next_beat_time - time.time()

            # Sleep until the next beat, or a minimum amount to prevent busy-wait
            sleep_duration = max(0.001, time_to_next_beat)
            time.sleep(sleep_duration)

    def update_beat_indicator(self, is_accent: bool) -> bool:
        """
        Updates the beat indicator label's color via GLib.idle_add.

        Args:
            is_accent: True if the current beat is accented, False otherwise.

        Returns:
            False, as required by GLib.idle_add callbacks.
        """
        color = ACCENT_COLOR if is_accent else NORMAL_COLOR # Use constants
        self.beat_indicator.set_markup(f'<span size="xx-large" foreground="{color}">●</span>')
        return False   # This is required for GLib.idle_add

    def show_error_dialog(self, message: str) -> None:
        """
        Displays an error message dialog to the user.

        Ensures the dialog is shown on the main GTK thread.

        Args:
            message: The error message string to display.
        """
        # This should check if we're in the main thread
        if threading.current_thread() is not threading.main_thread():
             GLib.idle_add(self.show_error_dialog, message)
             return

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

    def cleanup(self) -> None:
        """
        Cleans up resources before the application exits.

        Stops the metronome thread and quits Pygame. Ensures pygame.quit()
        is called even if the thread join times out.
        """
        thread_to_join = None
        with self._lock:
            self.is_playing = False # Signal thread to stop
            if self.metronome_thread is not None and self.metronome_thread.is_alive():
                thread_to_join = self.metronome_thread

        try:
           if thread_to_join:
               thread_to_join.join(THREAD_JOIN_TIMEOUT) # Wait for thread outside lock
        finally:
           pygame.quit() # Ensure pygame quits even if join fails/times out

def main() -> None:
    """
    Initializes Pygame mixer, creates the MetronomeWindow,
    and starts the GTK main loop. Handles initialization errors.
    """
    # Initialize pygame mixer before creating window
    try:
        # Use recommended buffer size for better performance/latency
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    except pygame.error as e:
        print(f"Fatal Error: Could not initialize sound system: {e}")
        print("MetroKnome cannot run without audio. Exiting.")
        return # Exit if mixer fails

    try:
        win = MetronomeWindow()
        win.connect("destroy", lambda x: win.cleanup() or Gtk.main_quit())
        win.show_all()
        Gtk.main()
    except RuntimeError as e:
        print(f"Fatal Error: Could not initialize MetronomeWindow: {e}")
        pygame.quit() # Ensure pygame is quit if window creation fails

if __name__ == "__main__":
    main()