import numpy as np
import pywt  # For wavelet transforms
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.io import loadmat

# Load the .mat file
data = loadmat('103m_MIT_BIH.mat')
ecgsig = data['val'].flatten() / 200  # Normalize similar to MATLAB

# Define sampling rate
Fs = 250  # Set the sampling rate to 250 Hz
t = np.arange(len(ecgsig))  # Sample indices
tx = t / Fs  # Time vector in seconds

# Perform a 4-level stationary wavelet decomposition using 'sym4'
coeffs = pywt.swt(ecgsig, 'sym4', level=4)

# Set all levels to zero arrays except for d3 and d4
coeffs_for_reconstruction = []
for i, (a, d) in enumerate(coeffs):
    if i in [2, 3]:  # Keep d3 and d4 coefficients as is
        coeffs_for_reconstruction.append((np.zeros_like(a), d))
    else:  # Zero out other coefficients
        coeffs_for_reconstruction.append((np.zeros_like(a), np.zeros_like(d)))

# Reconstruct the signal with selected coefficients using ISWT
reconstructed_signal = pywt.iswt(coeffs_for_reconstruction, 'sym4')

# Process the signal to detect R-peaks
y = np.abs(reconstructed_signal) ** 2  # Magnitude square
avg = np.mean(y)
Rpeaks, properties = find_peaks(y, height=8 * avg, distance=50)
nohb = len(Rpeaks)  # Number of beats
timelimit = len(ecgsig) / Fs
hbpermin = (nohb * 60) / timelimit  # Heart rate in BPM
print(f"Heart Rate = {hbpermin:.2f} BPM")

if 60 <= hbpermin <= 100:
    print(f"Heart Rate = {hbpermin:.2f} BPM (Normal)")
elif hbpermin < 60:
    print(f"Heart Rate = {hbpermin:.2f} BPM (Low - Consult a doctor if symptomatic)")
elif hbpermin > 100:
    print(f"Heart Rate = {hbpermin:.2f} BPM (High - Monitor or consult a doctor)")

# Plot the results
plt.figure(figsize=(10, 6))

# Original ECG Signal
plt.subplot(2, 1, 1)
plt.plot(tx, ecgsig)
plt.xlim([0, timelimit])
plt.xlabel('Seconds')
plt.title('ECG Signal')
plt.grid(True)

# Processed Signal with R-peaks
plt.subplot(2, 1, 2)
plt.plot(t, y)
plt.plot(Rpeaks, y[Rpeaks], 'ro')  # Mark detected peaks
plt.xlim([0, len(ecgsig)])
plt.xlabel('Samples')
plt.title(f'R Peaks found and Heart Rate: {hbpermin:.2f} BPM')
plt.grid(True)

plt.tight_layout()
plt.show()

