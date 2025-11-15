import pygame
import time
import sys

def play_midi(file_path):
    try:
        # Initialize the mixer
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        print(f"Playing {file_path}...")
        
        # Play the MIDI file
        pygame.mixer.music.play()
        
        # Wait until the music finishes playing
        while pygame.mixer.music.get_busy():
            time.sleep(1)
            
        print("Playback finished.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Check if the MIDI file path is provided
    if len(sys.argv) != 2:
        print("Usage: python play_midi.py <path_to_midi_file>")
        sys.exit(1)
    
    midi_file = sys.argv[1]
    play_midi(midi_file)
