# download.py
import subprocess
import os
import re

def slugify_url(url: str) -> str:
    match = re.search(r"v=([^&]+)", url)
    if match:
        slug = match.group(1)
    else:
        slug = url.strip().split('/')[-1]
    slug = re.sub(r'[^a-zA-Z0-9_-]', '_', slug)
    return slug

def download_mp3(url: str, base_dir: str) -> (str, str):
    slug = slugify_url(url)
    target_dir = os.path.join(base_dir, slug)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        
    mp3_pattern = os.path.join(target_dir, "%(title)s.%(ext)s")
    
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--extractor-args", "youtube:player_client=android",
        "-o", mp3_pattern,
        url
    ]
    subprocess.run(cmd, check=True)

    mp3_files = [f for f in os.listdir(target_dir) if f.lower().endswith('.mp3')]
    if not mp3_files:
        raise FileNotFoundError("No MP3 file found after download.")
    
    mp3_filename = mp3_files[0]
    mp3_full_path = os.path.join(target_dir, mp3_filename)
    return target_dir, mp3_full_path
