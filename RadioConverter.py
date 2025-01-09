import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = ["pydub"]

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install(package)

from pydub import AudioSegment
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading

def format_time(seconds):
    """Convert seconds to a formatted string of hours, minutes, and seconds."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours}h {minutes}m {seconds}s"

def get_audio_lengths(folder):
    lengths = {}
    total_time = 0
    for filename in os.listdir(folder):
        if filename.endswith('.mp3'):
            audio_path = os.path.join(folder, filename)
            audio_segment = AudioSegment.from_file(audio_path)
            lengths[filename] = len(audio_segment) / 1000.0  
            total_time += lengths[filename]
    return lengths, total_time

def check_folder_a(folder):
    if folder:
        try:
            lengths, total_time = get_audio_lengths(folder)
            total_time_label_a.config(text=f"Total time: {format_time(total_time)}")
        except Exception as e:
            total_time_label_a.config(text="Total time: N/A")
            insert_and_scroll(f"Error calculating total time for Fallout Default: {e}\n")

def check_folder_b(folder):
    if folder:
        try:
            lengths, total_time = get_audio_lengths(folder)
            total_time_label_b.config(text=f"Total time: {format_time(total_time)}")
        except Exception as e:
            total_time_label_b.config(text="Total time: N/A")
            insert_and_scroll(f"Error calculating total time for Your Songs: {e}\n")

def insert_and_scroll(text):
    history_text.insert(tk.END, text)
    history_text.see(tk.END)

def reorganize_audio_files_with_limits(folder_a, folder_b, folder_c, progress_var, history_text):
    os.makedirs(folder_c, exist_ok=True)
    insert_and_scroll("Starting audio processing...\n")
    
    list_a, total_a_time = get_audio_lengths(folder_a)
    insert_and_scroll(f"Total time from Fallout Default: {format_time(total_a_time)}\n")
    
    music_segments = {}
    
    for filename in os.listdir(folder_b):
        if filename.endswith('.mp3'):
            audio_path = os.path.join(folder_b, filename)
            music_segments[filename] = AudioSegment.from_file(audio_path)

    total_b_time = sum(len(segment) / 1000.0 for segment in music_segments.values())
    insert_and_scroll(f"Total time from Your Songs: {format_time(total_b_time)}\n")
    
    progress_var.set(0)
    used_b_filenames = []
    remaining_time_from_a = total_a_time
    total_files = len(list_a)
    
    for idx, (filename, duration) in enumerate(list_a.items()):
        target_duration = duration * 1000

        if 'prelude' in filename.lower():
            insert_and_scroll(f"Including {filename} (Prelude file) unchanged.\n")
            audio_segment = AudioSegment.from_file(os.path.join(folder_a, filename))
            audio_segment.export(os.path.join(folder_c, filename), format="mp3")
            remaining_time_from_a -= duration 
            continue

        combined_audio = AudioSegment.silent(duration=0)
        used_segments = []

        for b_filename, segment in music_segments.items():
            if b_filename not in used_b_filenames and len(combined_audio) < target_duration:
                combined_audio += segment
                used_segments.append(b_filename)
                used_b_filenames.append(b_filename)
                
            if len(combined_audio) >= target_duration:
                break

        if len(combined_audio) > target_duration:
            combined_audio = combined_audio[:target_duration]

        if len(combined_audio) > 0:
            combined_audio.export(os.path.join(folder_c, filename), format="mp3")
            insert_and_scroll(f"Replaced {filename} with combined audio from Your Songs using: {', '.join(used_segments)}.\n")
            remaining_time_from_a -= (len(combined_audio) / 1000.0)
        else:
            original_audio_path = os.path.join(folder_a, filename)
            if os.path.exists(original_audio_path):
                AudioSegment.from_file(original_audio_path).export(os.path.join(folder_c, filename), format="mp3")
                insert_and_scroll(f"No segments available for {filename}. Original file included in output.\n")

        progress_var.set((idx + 1) / total_files * 100)
        root.update_idletasks()

    for b_filename, segment in music_segments.items():
        if b_filename not in used_b_filenames:
            segment.export(os.path.join(folder_c, b_filename), format="mp3")
            insert_and_scroll(f"Included unused file from Your Songs: {b_filename}\n")

    if total_b_time < total_a_time:
        insert_and_scroll("WARNING: Total time from Your Songs is lower than from Fallout Default.\n")

    insert_and_scroll("Processing complete. Files saved in: " + folder_c + "\n")

def process_audio_in_thread(folder_a, folder_b, folder_c, progress_var, history_text):
    """Run the audio processing in a separate thread."""
    try:
        reorganize_audio_files_with_limits(folder_a, folder_b, folder_c, progress_var, history_text)
    except Exception as e:
        insert_and_scroll(f"Error during processing: {e}\n")

def start_processing():
    folder_a = entry_a.get()
    folder_b = entry_b.get()
    folder_c = entry_c.get()

    if not all([folder_a, folder_b, folder_c]):
        messagebox.showwarning("Input Error", "Please select all folders.")
        return

    history_text.delete(1.0, tk.END)
    
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

    processing_thread = threading.Thread(target=process_audio_in_thread, args=(folder_a, folder_b, folder_c, progress_var, history_text))
    processing_thread.start()

def browse_folder_a():
    folder_a = filedialog.askdirectory(title="Select Fallout Default Folder")
    entry_a.delete(0, tk.END)
    entry_a.insert(0, folder_a)
    check_folder_a(folder_a)

def browse_folder_b():
    folder_b = filedialog.askdirectory(title="Select Your Songs Folder")
    entry_b.delete(0, tk.END)
    entry_b.insert(0, folder_b)
    check_folder_b(folder_b)

def browse_folder_c():
    folder_c = filedialog.askdirectory(title="Select Output Folder")
    entry_c.delete(0, tk.END)
    entry_c.insert(0, folder_c)


root = tk.Tk()
root.title("Audio Reorganizer")


default_folder_a = 'FalloutSongsClassics'
default_folder_b = 'YourSongs'
default_folder_c = 'Output'


tk.Label(root, text="Fallout Default Folder:").grid(row=0, column=0, padx=10, pady=10)
entry_a = tk.Entry(root, width=40)
entry_a.grid(row=0, column=1, padx=10, pady=10)
entry_a.insert(0, default_folder_a)

total_time_label_a = tk.Label(root, text="Total time: N/A")
total_time_label_a.grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Your Songs Folder:").grid(row=1, column=0, padx=10, pady=10)
entry_b = tk.Entry(root, width=40)
entry_b.grid(row=1, column=1, padx=10, pady=10)
entry_b.insert(0, default_folder_b)

total_time_label_b = tk.Label(root, text="Total time: N/A")
total_time_label_b.grid(row=1, column=2, padx=10, pady=10)

tk.Label(root, text="Output Folder:").grid(row=2, column=0, padx=10, pady=10)
entry_c = tk.Entry(root, width=40)
entry_c.grid(row=2, column=1, padx=10, pady=10)
entry_c.insert(0, default_folder_c)

tk.Button(root, text="Process Audio", command=start_processing).grid(row=3, column=1, padx=10, pady=20)

history_text = scrolledtext.ScrolledText(root, width=60, height=15, state='normal')
history_text.grid(row=5, column=0, columnspan=4, padx=10, pady=10)

check_folder_a(default_folder_a)  
check_folder_b(default_folder_b) 


root.mainloop()
