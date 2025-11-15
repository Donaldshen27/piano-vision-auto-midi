import subprocess, sys

def play_midi(midi_path: str) -> None:
    cmd = [sys.executable, "play_midi.py", midi_path.replace('\\', '/')]
    subprocess.run(cmd, check=True)
