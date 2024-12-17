import os
import threading
import tkinter.messagebox
from tkinter import *
from tkinter import ttk
import numpy as np
import pywt
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, butter, lfilter, savgol_filter
from collections import deque
import serial
import pygame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Serial setup for real-time ECG data acquisition
ser = serial.Serial('COM6', 115200, timeout=1)
ser.flush()

# Parameters for Butterworth filter
def butter_lowpass(cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order)
    return lfilter(b, a, data)

# Parameters for wavelet analysis
sampling_rate = 100.0  # Hz
cutoff_frequency = 20  # Hz
ecg_buffer = deque(maxlen=1000)
processed_signal_buffer = deque(maxlen=1000)

# Music Player Initialization
pygame.mixer.init()
playlist = [
    {"path": r"C:/Users/khanh/Downloads/Short Song (English Song) [W Lyrics] 30 seconds.mp3", "condition": "<60"},
    {"path": r"C:/Users/khanh/Downloads/SHORT MUSIC - No Copyright Music - Royalty-free Music For Background 2023.mp3", "condition": "60-100"},
    {"path": r"C:/Users/khanh/Downloads/DSP-Fix1/DSP-Fix1/Downloads/DSP/Python-Music-Player-master/100+/Let It Be (Remastered 2009).mp3", "condition": ">100"}
]
current_song_index = -1

# Functions for heart rate and music selection
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
        if index != current_song_index:
            song_path = playlist[index]["path"]
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            current_song_index = index
            statusbar['text'] = f"Playing: {os.path.basename(song_path)}"
    except IndexError:
        tkinter.messagebox.showerror("Error", "Invalid song index or playlist is empty.")

def pause_song():
    pygame.mixer.music.pause()
    statusbar['text'] = "Music Paused"

def resume_song():
    pygame.mixer.music.unpause()
    statusbar['text'] = "Music Resumed"

def stop_song():
    pygame.mixer.music.stop()
    statusbar['text'] = "Music Stopped"

def compute_heart_rate(ecg_signal, fs):
    coeffs = pywt.swt(ecg_signal, 'sym4', level=3)
    coeffs_for_reconstruction = [
        (np.zeros_like(a), d if i in [2, 3] else np.zeros_like(d))
        for i, (a, d) in enumerate(coeffs)
    ]
    reconstructed_signal = pywt.iswt(coeffs_for_reconstruction, 'sym4')
    y = np.abs(reconstructed_signal) ** 2
    avg = np.mean(y)
    Rpeaks, _ = find_peaks(y, height=8 * avg, distance=int(fs / 2))
    heart_rate = (len(Rpeaks) * 60) / (len(ecg_signal) / fs)
    return heart_rate, y, Rpeaks

# GUI setup
root = Tk()
root.geometry("900x700")
root.title("Real-Time ECG and Music Player")

statusbar = Label(root, text="Welcome to the ECG Music App", relief=SUNKEN, anchor=W, font='Times 10 italic')
statusbar.pack(side=BOTTOM, fill=X)

fig, ax = plt.subplots(2, 1, figsize=(8, 6))
ax[0].set_ylim(0, 2000)
ax[0].set_xlim(0, 1000)
ecg_line, = ax[0].plot([], [], lw=0.5)
ax[0].set_title("Real-Time ECG Signal")
ax[0].set_xlabel("Time (samples)")
ax[0].set_ylabel("Amplitude")
ax[0].grid(True)

ax[1].set_xlim(0, 1000)
ax[1].set_ylim(0, 100)
processed_line, = ax[1].plot([], [], lw=0.5)
ax[1].set_title("Heart Rate Peaks")
ax[1].set_xlabel("Time (samples)")
ax[1].grid(True)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side=TOP, fill=BOTH, expand=True)

def update_data():
    global ecg_buffer, processed_signal_buffer
    if ser.in_waiting > 0:
        try:
            data = ser.readline().decode('utf-8').strip()
            raw_value = float(data)
            ecg_buffer.append(raw_value)

            if len(ecg_buffer) >= 1000:
                filtered_signal = butter_lowpass_filter(list(ecg_buffer), cutoff_frequency, sampling_rate)
                filtered_signal = savgol_filter(filtered_signal, window_length=15, polyorder=3)
                heart_rate, processed_signal, Rpeaks = compute_heart_rate(filtered_signal, sampling_rate)
                if processed_signal is not None:
                    processed_signal_buffer.clear()
                    processed_signal_buffer.extend(processed_signal)
                    play_song(select_song_by_hr(heart_rate))
                    processed_line.set_data(range(len(processed_signal_buffer)), processed_signal_buffer)
                    ax[1].clear()
                    ax[1].plot(range(len(processed_signal_buffer)), processed_signal_buffer, lw=0.5)
                    for peak in Rpeaks:
                        ax[1].plot(peak, processed_signal[peak], 'ro')
                    statusbar['text'] = f"Heart Rate: {heart_rate:.2f} BPM"

            ecg_line.set_data(range(len(ecg_buffer)), ecg_buffer)
            ax[0].clear()
            ax[0].plot(range(len(ecg_buffer)), ecg_buffer, lw=0.5)
            ax[0].set_ylim(1250, 3000)
            ax[0].set_xlim(0, 1000)

            canvas.draw()
        except ValueError:
            pass

    root.after(10, update_data)

def start_measurement():
    update_data()

button_frame = Frame(root)
button_frame.pack(pady=20)

start_button = ttk.Button(button_frame, text="Start", command=start_measurement)
start_button.grid(row=0, column=0, padx=10)

pause_button = ttk.Button(button_frame, text="Pause Music", command=pause_song)
pause_button.grid(row=0, column=1, padx=10)

resume_button = ttk.Button(button_frame, text="Resume Music", command=resume_song)
resume_button.grid(row=0, column=2, padx=10)

stop_button = ttk.Button(button_frame, text="Stop Music", command=stop_song)
stop_button.grid(row=0, column=3, padx=10)

def on_closing():
    if ser:
        ser.close()
    pygame.mixer.music.stop()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop() 
