import subprocess

def convert_to_midi(mp3_path: str, midi_path: str) -> None:
    cmd = [
        "transkun",
        mp3_path,
        midi_path,
        "--device", "cuda"
    ]
    subprocess.run(cmd, check=True)
