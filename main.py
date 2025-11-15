# main.py
import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import threading
import queue
import sys

from download import download_mp3
from convert import convert_to_midi
from playback import play_midi

root = tk.Tk()
root.title("MP3 to MIDI Converter")
root.configure(bg="#f2f2f2")
root.geometry("600x400")

label_font = ("Helvetica", 11)
button_font = ("Helvetica", 10, "bold")

# Directory Label & Entry
dir_label = tk.Label(root, text="Enter the Music Download Directory:", font=label_font, bg="#f2f2f2")
dir_label.pack(pady=(20,5))

dir_entry = tk.Entry(root, width=60)
dir_entry.insert(0, r"C:\Users\a11a2\Music\ ")  # Default directory
dir_entry.pack(pady=5)

# URL Label & Entry
url_label = tk.Label(root, text="Enter the YouTube URL:", font=label_font, bg="#f2f2f2")
url_label.pack(pady=(20,5))

url_entry = tk.Entry(root, width=60)
url_entry.pack(pady=5)

# Progress/Log Area
log_label = tk.Label(root, text="Progress Log:", font=label_font, bg="#f2f2f2")
log_label.pack(pady=(20,5))

log_text = tk.Text(root, width=70, height=10, state='normal')
log_text.pack(pady=5)

def log_message(message: str):
    # Direct logging: insert text at end
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)

midi_path_var = tk.StringVar()
midi_path_entry = tk.Entry(root, textvariable=midi_path_var, width=60, fg='grey')
midi_path_entry.pack(pady=(5,0))

def copy_to_clipboard():
    midi_path = midi_path_entry.get().strip()
    root.clipboard_clear()
    root.clipboard_append(midi_path)
    messagebox.showinfo("Copied", "MIDI path copied to clipboard.")

copy_button = tk.Button(root, text="Copy MIDI Path", font=button_font, bg="#9c27b0", fg="white", command=copy_to_clipboard)
copy_button.pack_forget()

play_button = tk.Button(root, text="Play MIDI", font=button_font, bg="#2196f3", fg="white")
play_button.pack_forget()

# Queue for thread-safe logging from background thread
log_queue = queue.Queue()

def process_log_queue():
    while True:
        try:
            msg = log_queue.get_nowait()
        except queue.Empty:
            break
        else:
            log_message(msg)
    root.after(100, process_log_queue)  # Check again in 100ms

root.after(100, process_log_queue)

def background_conversion(url, base_dir):
    try:
        log_queue.put("Creating folder and downloading MP3...")
        target_dir, mp3_full_path = download_mp3(url, base_dir)
        log_queue.put(f"Folder created: {target_dir}")
        log_queue.put("Download complete.")
        
        midi_filename = os.path.splitext(os.path.basename(mp3_full_path))[0] + ".mid"
        midi_full_path = os.path.join(target_dir, midi_filename)
        
        log_queue.put("Converting MP3 to MIDI...")
        convert_to_midi(mp3_full_path, midi_full_path)
        log_queue.put("Conversion complete.")
        
        # Rename folder to midi file name without extension
        midi_name_no_ext = os.path.splitext(midi_filename)[0]
        new_folder_path = os.path.join(base_dir, midi_name_no_ext)
        os.rename(target_dir, new_folder_path)
        
        # Update midi_full_path after rename
        midi_full_path = os.path.join(new_folder_path, midi_filename)
        
        # Update GUI elements from main thread
        def update_gui():
            midi_path_var.set(midi_full_path)
            copy_button.pack(side="top", pady=(10,5))
            play_button.config(command=lambda: play_midi(midi_full_path))
            play_button.pack(side="top", pady=5)
            convert_button.config(state='normal')
        
        root.after(0, update_gui)
        log_queue.put("Process finished successfully.")
        
    except subprocess.CalledProcessError as e:
        error_msg = f"An error occurred during an external process: {e}"
        log_queue.put(error_msg)
        root.after(0, lambda: [messagebox.showerror("Error", error_msg), convert_button.config(state='normal')])
    except Exception as e:
        error_msg = str(e)
        log_queue.put(error_msg)
        root.after(0, lambda: [messagebox.showerror("Error", error_msg), convert_button.config(state='normal')])

def start_conversion_thread():
    url = url_entry.get().strip()
    base_dir = dir_entry.get().strip()
    
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL.")
        return
    if not base_dir:
        messagebox.showerror("Error", "Please enter a directory.")
        return
    
    convert_button.config(state='disabled')
    log_text.delete('1.0', tk.END)
    log_queue.put("Starting conversion process...")
    
    thread = threading.Thread(target=background_conversion, args=(url, base_dir), daemon=True)
    thread.start()

convert_button = tk.Button(root, text="Convert to MIDI", font=button_font, bg="#4caf50", fg="white", command=start_conversion_thread)
convert_button.pack(pady=(10,5))

root.mainloop()
