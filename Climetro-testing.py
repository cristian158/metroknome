import click
import pygame
import time
import threading
import queue

class Metronome:
    def __init__(self, bpm, time_signature, volume):
        pygame.mixer.init()
        self.normal_click = pygame.mixer.Sound("/home/spweedy/TESTS/Metro-knome/tick.wav")
        self.accent_click = pygame.mixer.Sound("/home/spweedy/TESTS/Metro-knome/tock.wav")
        
        self.bpm = bpm
        self.time_signature = time_signature
        self.volume = volume
        self.is_playing = False
        self.beat_count = 0

        self.update_volume()

    def update_volume(self):
        self.normal_click.set_volume(self.volume)
        self.accent_click.set_volume(self.volume)

    def start(self):
        self.is_playing = True
        self.beat_count = 0
        threading.Thread(target=self.run, daemon=True).start()

    def stop(self):
        self.is_playing = False

    def run(self):
        while self.is_playing:
            interval = 60 / self.bpm
            if self.beat_count % self.time_signature[0] == 0:
                self.accent_click.play()
                print("\r\033[91m●\033[0m" + "○" * (self.time_signature[0] - 1), end="", flush=True)
            else:
                self.normal_click.play()
                print("\r" + "○" * (self.beat_count % self.time_signature[0]) + "\033[94m●\033[0m" + "○" * (self.time_signature[0] - self.beat_count % self.time_signature[0] - 1), end="", flush=True)
            self.beat_count += 1
            time.sleep(interval)

def print_status(metronome):
    print(f"\nCurrent settings:")
    print(f"BPM: {metronome.bpm}")
    print(f"Time signature: {metronome.time_signature[0]}/{metronome.time_signature[1]}")
    print(f"Volume: {metronome.volume:.2f}")

def input_thread(input_queue):
    while True:
        input_queue.put(input().strip().lower())

@click.command()
@click.option('-b', '--bpm', default=120, help='Beats per minute')
@click.option('-t', '--time-signature', default='4/4', help='Time signature (e.g., 4/4, 3/4)')
@click.option('-v', '--volume', default=0.5, help='Volume (0.0 - 1.0)')
def main(bpm, time_signature, volume):
    beats, unit = map(int, time_signature.split('/'))
    metronome = Metronome(bpm, (beats, unit), volume)
    
    print(f"Starting metronome at {bpm} BPM, {beats}/{unit} time signature")
    print("Commands:")
    print("  q: Quit")
    print("  b <value>: Change BPM")
    print("  t <beats>/<unit>: Change time signature")
    print("  v <value>: Change volume (0.0 - 1.0)")
    print("  s: Show current settings")
    
    metronome.start()
    
    input_queue = queue.Queue()
    threading.Thread(target=input_thread, args=(input_queue,), daemon=True).start()

    try:
        while True:
            try:
                command = input_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if command == 'q':
                metronome.stop()
                break
            elif command.startswith('b '):
                try:
                    new_bpm = int(command.split()[1])
                    metronome.bpm = new_bpm
                    print(f"\nBPM changed to {new_bpm}")
                except (IndexError, ValueError):
                    print("\nInvalid BPM. Usage: b <value>")
            elif command.startswith('t '):
                try:
                    beats, unit = map(int, command.split()[1].split('/'))
                    metronome.time_signature = (beats, unit)
                    metronome.beat_count = 0
                    print(f"\nTime signature changed to {beats}/{unit}")
                except (IndexError, ValueError):
                    print("\nInvalid time signature. Usage: t <beats>/<unit>")
            elif command.startswith('v '):
                try:
                    new_volume = float(command.split()[1])
                    if 0 <= new_volume <= 1:
                        metronome.volume = new_volume
                        metronome.update_volume()
                        print(f"\nVolume changed to {new_volume:.2f}")
                    else:
                        print("\nVolume must be between 0.0 and 1.0")
                except (IndexError, ValueError):
                    print("\nInvalid volume. Usage: v <value>")
            elif command == 's':
                print_status(metronome)
            else:
                print("\nUnknown command. Use q, b, t, v, or s.")
    except KeyboardInterrupt:
        pass
    finally:
        metronome.stop()
        print("\nMetronome stopped.")

if __name__ == '__main__':
    main()

