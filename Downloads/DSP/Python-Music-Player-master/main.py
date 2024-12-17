import os
import threading
import time
import tkinter.messagebox
from tkinter import *
from tkinter import filedialog
import threading 
from tkinter import ttk
from ttkthemes import themed_tk as tk

from mutagen.mp3 import MP3
from pygame import mixer

import numpy as np
import scipy.io  # For loading MATLAB files
import pywt  # For wavelet transforms
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.io import loadmat
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Music Player Initialization
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
playlist = []

# Playlists
playlist60 = [
    r"C:/Users/PC/Downloads/DSP/Python-Music-Player-master/-60/Debussy - Clair de Lune.mp3",
    r"C:/Users/PC/Downloads/DSP/Python-Music-Player-master/-60/Marconi Union - Weightless (Official Video) - JustMusicTV (youtube).mp3"
]
playlist60_100 = [
    r"C:/Users/PC/Downloads/DSP/Python-Music-Player-master/60-100/Breathe Me.mp3",
    r"C:/Users/PC/Downloads/DSP/Python-Music-Player-master/60-100/Adele - Someone Like You (Official Music Video).mp3",
    r"C:/Users/PC/Downloads/DSP/Python-Music-Player-master/60-100/Coldplay - Yellow (Official Video).mp3"
]
playlist100 = [
    r"C:/Users/PC/Downloads/DSP/Python-Music-Player-master/100+/Let It Be (Remastered 2009).mp3",
    r"C:/Users/PC/Downloads/DSP/Python-Music-Player-master/100+/Coldplay - Fix You (Official Video).mp3",
    r"C:/Users/PC/Downloads/DSP/Python-Music-Player-master/100+/Radiohead - No Surprises.mp3"
]

def browse_file():
    global filename_path
    filename_path = filedialog.askopenfilename()
    add_to_playlist(filename_path)
    mixer.music.queue(filename_path)


def add_to_playlist(filename):
    filename = os.path.basename(filename)
    index = 0
    playlistbox.insert(index, filename)
    playlist.insert(index, filename_path)
    index += 1
heart_rate = 0

hbpermin = 0 
def plot_chart():
    # Load the .mat file
    data = loadmat('200m_MIT_BIH.mat')
    ecgsig = data['val'].flatten() / 200  # Normalize similar to MATLAB

    Fs = 250  # Fixed sampling rate
    t = np.arange(len(ecgsig))  # Sample indices
    tx = t / Fs  # Time vector in seconds

    coeffs = pywt.swt(ecgsig, 'sym4', level=4)
    coeffs_for_reconstruction = []
    for i, (a, d) in enumerate(coeffs):
        if i in [2, 3]:  # Keep d3 and d4 coefficients
            coeffs_for_reconstruction.append((np.zeros_like(a), d))
        else:
            coeffs_for_reconstruction.append((np.zeros_like(a), np.zeros_like(d)))

    reconstructed_signal = pywt.iswt(coeffs_for_reconstruction, 'sym4')
    y = np.abs(reconstructed_signal) ** 2  # Magnitude square
    avg = np.mean(y)
    Rpeaks, properties = find_peaks(y, height=8 * avg, distance=50)
    nohb = len(Rpeaks)  # Number of beats
    timelimit = len(ecgsig) / Fs
    hbpermin = (nohb * 60) / timelimit  # Heart rate in BPM

    # Determine the heart rate condition
    if 60 <= hbpermin <= 100:
        message = f"Heart Rate = {hbpermin:.2f} BPM (Normal)"
    elif hbpermin < 60:
        message = f"Heart Rate = {hbpermin:.2f} BPM (Low - Consult a doctor if symptomatic)"
    elif hbpermin > 100:
        message = f"Heart Rate = {hbpermin:.2f} BPM (High - Monitor or consult a doctor)"
    
    # Create the figure
    fig, axs = plt.subplots(2, 1, figsize=(8, 6))

    # Original ECG Signal
    axs[0].plot(tx, ecgsig)
    axs[0].set_xlim([0, timelimit])
    axs[0].set_xlabel('Seconds')
    axs[0].set_title('ECG Signal')
    axs[0].grid(True)

    # Processed Signal with R-peaks
    axs[1].plot(t, y)
    axs[1].plot(Rpeaks, y[Rpeaks], 'ro')  # Mark detected peaks
    axs[1].set_xlim([0, len(ecgsig)])
    axs[1].set_xlabel('Samples')
    axs[1].set_title(f'R Peaks found and Heart Rate: {message} BPM')
    axs[1].grid(True)

    plt.tight_layout()

    # Embed the plot into the Tkinter frame
    for widget in chart_frame.winfo_children():
        widget.destroy()  # Clear the frame before rendering a new chart

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)
    
    hbpermin = int(hbpermin)
    load_and_play_playlist(hbpermin)


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

# Root Window - StatusBar, LeftFrame, RightFrame
# LeftFrame - The listbox (playlist)
# RightFrame - TopFrame,MiddleFrame and the BottomFrame

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
    # mixer.music.get_busy(): - Returns FALSE when we press the stop button (music stop playing)
    # Continue - Ignores all of the statements below it. We check if music is paused or not.
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


def play_music():
    global paused

    if paused:
        mixer.music.unpause()
        statusbar['text'] = "Music Resumed"
        paused = FALSE
    else:
        try:
            stop_music()
            time.sleep(1)
            selected_song = playlistbox.curselection()
            selected_song = int(selected_song[0])
            play_it = playlist[selected_song]
            mixer.music.load(play_it)
            mixer.music.play()
            statusbar['text'] = "Playing music" + ' - ' + os.path.basename(play_it)
            show_details(play_it)
        except:
            tkinter.messagebox.showerror('File not found', 'Melody could not find the file. Please check again.')

def load_and_play_playlist(hr):
    heart_rate = int(hr)
    global playlistbox, playlist
    # Clear existing playlist
    playlistbox.delete(0, END)

    # Select the appropriate playlist
    if heart_rate < 60:
        playlist = playlist60
    elif 60 <= heart_rate <= 100:
        playlist = playlist60_100
    else:
        playlist = playlist100

    # Add songs to playlistbox
    for song_path in playlist:
        playlistbox.insert(END, os.path.basename(song_path))

    # Play the first song in the playlist
    play_song(0)

# Function to play a specific song
def play_song(index):
    song_path = playlist[index]
    mixer.music.load(song_path)
    mixer.music.play()
def stop_music():
    mixer.music.stop()
    statusbar['text'] = "Music Stopped"


paused = FALSE


def pause_music():
    global paused
    paused = TRUE
    mixer.music.pause()
    statusbar['text'] = "Music Paused"


def rewind_music():
    play_music()
    statusbar['text'] = "Music Rewinded"

def start_chart_plot():
    chart_thread = threading.Thread(target=plot_chart)
    chart_thread.start()

def set_vol(val):
    volume = float(val) / 100
    mixer.music.set_volume(volume)
    # set_volume of mixer takes value only from 0 to 1. Example - 0, 0.1,0.55,0.54.0.99,1


muted = FALSE


def mute_music():
    global muted
    if muted:  # Unmute the music
        mixer.music.set_volume(0.7)
        volumeBtn.configure(image=volumePhoto)
        scale.set(70)
        muted = FALSE
    else:  # mute the music
        mixer.music.set_volume(0)
        volumeBtn.configure(image=mutePhoto)
        scale.set(0)
        muted = TRUE


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

rewindPhoto = PhotoImage(file='images/rewind.png')
rewindBtn = ttk.Button(bottomframe, image=rewindPhoto, command=rewind_music)
rewindBtn.grid(row=0, column=0)

mutePhoto = PhotoImage(file='images/mute.png')
volumePhoto = PhotoImage(file='images/volume.png')
volumeBtn = ttk.Button(bottomframe, image=volumePhoto, command=mute_music)
volumeBtn.grid(row=0, column=1)

scale = ttk.Scale(bottomframe, from_=0, to=100, orient=HORIZONTAL, command=set_vol)
scale.set(70)  # implement the default value of scale when music player starts
mixer.music.set_volume(0.7)
scale.grid(row=0, column=2, pady=15, padx=30)


def on_closing():
    stop_music()
    root.destroy()

# Run the application
root.protocol("WM_DELETE_WINDOW", root.destroy)

start_chart_plot()



root.mainloop()
