import os
import threading
import time
import tkinter.messagebox
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from ttkthemes import themed_tk as tk
import pygame
from mutagen.mp3 import MP3
from pygame import mixer

import numpy as np
import pywt  # For wavelet transforms
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.io import loadmat
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Music Player Initialization
pygame.display.init()  # Initialize the pygame display
mixer.init()  # Initialize the mixer
root = tk.ThemedTk()
root.get_themes()                 # Returns a list of all themes that can be set
root.set_theme("radiance")        # Sets an available theme
root.state("zoomed")

statusbar = ttk.Label(root, text="Welcome to Melody", relief=SUNKEN, anchor=W, font='Times 10 italic')
statusbar.pack(side=BOTTOM, fill=X)

# Create the menubar
menubar = Menu(root)
root.config(menu=menubar)

# File Menu
subMenu = Menu(menubar, tearoff=0)
playlist = [
    {"path": r"C:/Users/khanh/Downloads/Short Song (English Song) [W Lyrics] 30 seconds.mp3", "condition": "<60"},
    {"path": r"C:/Users/khanh/Downloads/SHORT MUSIC - No Copyright Music - Royalty-free Music For Background 2023.mp3", "condition": "60-100"},
    {"path": r"C:/Users/khanh/Downloads/DSP-Fix1/DSP-Fix1/Downloads/DSP/Python-Music-Player-master/100+/Let It Be (Remastered 2009).mp3", "condition": ">100"}
]
ecg_files = [
    '100m_MIT_BIH.mat',
    'rec_1m_ECG_ID.mat',
    'rec_5m_ECG_ID.mat',
    # Add other files here...
]
def browse_file():
    global filename_path
    filename_path = filedialog.askopenfilename()
    mixer.music.queue(filename_path)

current_song_index = -1
paused = False
heart_rate = 0  # Global variable for heart rate

def select_song_by_hr(hr):
  
    if hr < 60:
        return 0
    elif 60 <= hr <= 100:
        return 1
    else:
        return 2

def play_song(index):
   
    global current_song_index
    try:
        song_path = playlist[index]["path"]
        mixer.music.load(song_path)
        mixer.music.play()
        statusbar['text'] = f"Playing: {os.path.basename(song_path)}"
        show_details(song_path)
        mixer.music.set_endevent(pygame.USEREVENT)
        print(f"Playing song: {os.path.basename(song_path)}")
    except IndexError:
        tkinter.messagebox.showerror("Error", "Invalid song index or playlist is empty.")

def handle_song_end():
    
    global current_song_index
    if current_song_index != -1:
        play_song(current_song_index)

def start_music_event_loop():
   
    while True:
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                handle_song_end()
        time.sleep(0.1)

def start_event_thread():
   
    event_thread = threading.Thread(target=start_music_event_loop, daemon=True)
    event_thread.start()

def update_heart_rate(new_heart_rate):
    
    global heart_rate, current_song_index
    heart_rate = new_heart_rate
    new_song_index = select_song_by_hr(heart_rate)

    if new_song_index != current_song_index:
        print(f"Heart rate changed to {heart_rate}, switching to song index {new_song_index}")
        current_song_index = new_song_index
        play_song(current_song_index)

def plot_chart(file_path):
    global heart_rate
    data = loadmat(file_path)  # Load the ECG data
    ecgsig = data['val'].flatten() / 200  # Normalize the ECG signal
    Fs = 250  # Sampling frequency
    t = np.arange(len(ecgsig))
    tx = t / Fs

    # Wavelet transform for signal processing
    coeffs = pywt.swt(ecgsig, 'sym4', level=4)
    coeffs_for_reconstruction = [
        (np.zeros_like(a), d if i in [2, 3] else np.zeros_like(d)) for i, (a, d) in enumerate(coeffs)
    ]
    reconstructed_signal = pywt.iswt(coeffs_for_reconstruction, 'sym4')

    # Calculate the heart rate based on R-peaks
    y = np.abs(reconstructed_signal) ** 2
    avg = np.mean(y)
    Rpeaks, _ = find_peaks(y, height=8 * avg, distance=50)
    nohb = len(Rpeaks)
    timelimit = len(ecgsig) / Fs
    calculated_heart_rate = int((nohb * 60) / timelimit)

    # Update the heart rate and potentially change the song
    update_heart_rate(calculated_heart_rate)

    # Plotting the charts (optional for display)
    fig, axs = plt.subplots(2, 1, figsize=(8, 6))
    axs[0].plot(tx, ecgsig)
    axs[0].set_title('ECG Signal')
    axs[1].plot(t, y)
    axs[1].plot(Rpeaks, y[Rpeaks], 'ro')
    axs[1].set_title(f'Heart Rate: {heart_rate} BPM')
    plt.tight_layout()

    # Update the canvas to display the plot in the Tkinter window
    for widget in chart_frame.winfo_children():
        widget.destroy()
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

def display_files_sequentially(index=0):
    if index < len(ecg_files):
        file_path = ecg_files[index]
        plot_chart(file_path)
        # wait 10s before new file.mat
        root.after(10000, display_files_sequentially, index + 1)

def start_display_loop():
    threading.Thread(target=display_files_sequentially, daemon=True).start()


# play music 
def play_music():
    global paused
    if paused:
        mixer.music.unpause()
        paused = False
        statusbar['text'] = "Music Resumed"
    elif current_song_index != -1:
        play_song(current_song_index)
    else:
        tkinter.messagebox.showerror("Error", "No song selected or playlist is empty.")


def pause_music():
    global paused
    if not paused:
        mixer.music.pause()
        paused = True
        statusbar['text'] = "Music Paused"


def stop_music():
    mixer.music.stop()
    statusbar['text'] = "Music Stopped"


subMenu.add_command(label="Open", command=browse_file)
subMenu.add_command(label="Update Plot Chart", command=plot_chart)  # Added chart functionality
subMenu.add_command(label="Exit", command=root.destroy)

menubar.add_cascade(label="File", menu=subMenu)

# Add the rest of the existing functionality for music player...
def about_us():
    tkinter.messagebox.showinfo('About Melody', 'This is a music player build using Python Tkinter by @attreyabhatt')


subMenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="Help", menu=subMenu)
subMenu.add_command(label="About Us", command=about_us)

mixer.init()  # initializing the mixer

root.title("Melody")
root.iconbitmap(r'images/melody.ico')

leftframe = Frame(root)
leftframe.pack(side=LEFT, padx=30, pady=30)

playlistbox = Listbox(leftframe)
playlistbox.pack()

# Create a frame for the chart in the main window
chart_frame = Frame(root, relief=SUNKEN, borderwidth=2)
chart_frame.pack(side=RIGHT, fill=BOTH, expand=True)
def del_song():
    selected_song = playlistbox.curselection()
    selected_song = int(selected_song[0])
    playlistbox.delete(selected_song)
    playlist.pop(selected_song)

rightframe = Frame(root)
rightframe.pack(pady=30)

topframe = Frame(rightframe)
topframe.pack()

lengthlabel = ttk.Label(topframe, text='Total Length : --:--')
lengthlabel.pack(pady=5)

currenttimelabel = ttk.Label(topframe, text='Current Time : --:--', relief=GROOVE)
currenttimelabel.pack()


def show_details(play_song):
    file_data = os.path.splitext(play_song)

    if file_data[1] == '.mp3':
        audio = MP3(play_song)
        total_length = audio.info.length
    else:
        a = mixer.Sound(play_song)
        total_length = a.get_length()

    # div - total_length/60, mod - total_length % 60
    mins, secs = divmod(total_length, 60)
    mins = round(mins)
    secs = round(secs)
    timeformat = '{:02d}:{:02d}'.format(mins, secs)
    lengthlabel['text'] = "Total Length" + ' - ' + timeformat

    t1 = threading.Thread(target=start_count, args=(total_length,))
    t1.start()


def start_count(t):
    global paused
    current_time = 0
    while current_time <= t and mixer.music.get_busy():
        if paused:
            continue
        else:
            mins, secs = divmod(current_time, 60)
            mins = round(mins)
            secs = round(secs)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            currenttimelabel['text'] = "Current Time" + ' - ' + timeformat
            time.sleep(1)
            current_time += 1

middleframe = Frame(rightframe)
middleframe.pack(pady=30, padx=30)

playPhoto = PhotoImage(file='images/play.png')
playBtn = ttk.Button(middleframe, image=playPhoto, command=play_music)
playBtn.grid(row=0, column=0, padx=10)

stopPhoto = PhotoImage(file='images/stop.png')
stopBtn = ttk.Button(middleframe, image=stopPhoto, command=stop_music)
stopBtn.grid(row=0, column=1, padx=10)

pausePhoto = PhotoImage(file='images/pause.png')
pauseBtn = ttk.Button(middleframe, image=pausePhoto, command=pause_music)
pauseBtn.grid(row=0, column=2, padx=10)

# Bottom Frame for volume, rewind, mute etc.

bottomframe = Frame(rightframe)
bottomframe.pack()

mixer.music.set_volume(0.7)

def on_closing():
    stop_music()
    root.destroy()

# Run the application
root.protocol("WM_DELETE_WINDOW", root.destroy)
start_display_loop()
start_event_thread()
root.mainloop()
