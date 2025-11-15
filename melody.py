import os
import numpy as np
import librosa
import pretty_midi

def extract_melody(audio, sr):
    """
    Extracts melody notes using librosa's PYIN pitch tracking.
    Returns a list of tuples: (start_time, end_time, midi_pitch).
    """
    # Use librosa.pyin for fundamental frequency (f0) estimation.
    f0, voiced_flag, _ = librosa.pyin(audio, 
                                      fmin=librosa.note_to_hz('C2'),
                                      fmax=librosa.note_to_hz('C7'))
    # Get time stamps for each frame
    times = librosa.times_like(f0, sr=sr)
    
    notes = []
    current_note = None
    current_start = None

    # Iterate over frames and group contiguous voiced segments
    for time, pitch, voiced in zip(times, f0, voiced_flag):
        if voiced:
            if current_note is None:
                # Start a new note segment.
                current_note = pitch
                current_start = time
            else:
                # If the pitch changes significantly, finish the current note.
                if abs(pitch - current_note) > 1.0:  # threshold in Hz (adjust if needed)
                    end_time = time
                    midi_pitch = int(round(librosa.hz_to_midi(current_note)))
                    notes.append((current_start, end_time, midi_pitch))
                    current_note = pitch
                    current_start = time
        else:
            if current_note is not None:
                # End the current note when unvoiced
                end_time = time
                midi_pitch = int(round(librosa.hz_to_midi(current_note)))
                notes.append((current_start, end_time, midi_pitch))
                current_note = None
                current_start = None
    # Add any lingering note segment
    if current_note is not None:
        end_time = times[-1]
        midi_pitch = int(round(librosa.hz_to_midi(current_note)))
        notes.append((current_start, end_time, midi_pitch))
    return notes

def create_midi(melody_notes, output_midi_path):
    """
    Creates a MIDI file with a melody track (piano).
    """
    # Initialize PrettyMIDI object.
    pm = pretty_midi.PrettyMIDI()
    
    # Create piano instrument (Acoustic Grand Piano, program number 0).
    piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    melody_instrument = pretty_midi.Instrument(program=piano_program)
    
    # Add melody note events.
    for start, end, pitch in melody_notes:
        # Skip extremely short notes.
        if end - start < 0.05:
            continue
        note = pretty_midi.Note(velocity=100, pitch=pitch, start=start, end=end)
        melody_instrument.notes.append(note)
    
    pm.instruments.append(melody_instrument)
    pm.write(output_midi_path)

def main(input_audio_path):
    # Load the input audio (supports formats like MP3 or WAV).
    print("Loading audio...")
    y, sr = librosa.load(input_audio_path, sr=None)
    
    # Extract melody notes.
    print("Extracting melody...")
    melody_notes = extract_melody(y, sr)
    print("Extracted melody notes:")
    for note in melody_notes:
        print(f"Start: {note[0]:.2f}, End: {note[1]:.2f}, MIDI Pitch: {note[2]}")
    
    # Create MIDI file in the same directory as input file
    input_dir = os.path.dirname(input_audio_path)
    input_filename = os.path.splitext(os.path.basename(input_audio_path))[0]
    midi_path = os.path.join(input_dir, f"{input_filename}.mid")
    
    print(f"Creating MIDI file at {midi_path}...")
    create_midi(melody_notes, midi_path)
    print("MIDI file created successfully.")

if __name__ == '__main__':
    # import argparse
    # parser = argparse.ArgumentParser(
    #     description="Transcribe a song's melody into a piano rendition and output as a MIDI file."
    # )
    # parser.add_argument("input_audio", help="Path to the input audio file (e.g., mp3 or wav)")
    # args = parser.parse_args()
    # main(args.input_audio)
    main("testvocal.mp3")
