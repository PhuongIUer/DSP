import numpy as np
import scipy.io  # For loading MATLAB files
import pywt  # For wavelet transforms
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

from scipy.io import loadmat


import thingspeak

# Replace with your channel ID and read API key
channel_id = '2146196'
read_key = 'ZTXGJNPIUX2DRHVS'

channel = thingspeak.Channel(id=channel_id, api_key=read_key)
data1 = channel.get_field_last(field='1')  # Replace '1' with your field number
data2 = channel.get_field_last(field='2')  # Replace '1' with your field number
data3 = channel.get_field_last(field='3')  # Replace '1' with your field number
data4 = channel.get_field_last(field='4')  # Replace '1' with your field number
data5 = channel.get_field_last(field='5')  # Replace '1' with your field number
data6 = channel.get_field_last(field='6')  # Replace '1' with your field number
print("Temperature: %f \n" + data1)
print("Humidity: %f \n" + data2)
print("CO: %f \n" + data3)
print("CO2: %f \n" + data4)
print("UV: %f \n" + data5)
print("Dust: %f \n" + data6)



# Load the .mat file (adjust 'your_file.mat' as needed)
data = loadmat('rec_1m_ECG_ID.mat')
ecgsig = data['val'].flatten() / 200  # Normalize similar to MATLAB

Fs = int(input("Enter Sampling Rate: "))  # Manually input sampling rate
t = np.arange(len(ecgsig))  # Sample indices
tx = t / Fs  # Time vector in seconds
# Perform a 4-level wavelet decomposition using the 'sym4' wavelet

# coeffs = pywt.waverec(ecgsig, 'sym4', level=4)
#
# # Set all levels to None except for the desired coefficients (d3 and d4)
# coeffs_for_reconstruction = [np.zeros_like(coeffs[0]), np.zeros_like(coeffs[1]), coeffs[2], coeffs[3], np.zeros_like(coeffs[4])]
#
# # Reconstruct the signal with selected coefficients
# reconstructed_signal = pywt.waverec(coeffs_for_reconstruction, 'sym4')
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

y = np.abs(reconstructed_signal) ** 2  # Magnitude square
avg = np.mean(y)
Rpeaks, properties = find_peaks(y, height=8 * avg, distance=50)
nohb = len(Rpeaks)  # Number of beats
timelimit = len(ecgsig) / Fs
hbpermin = (nohb * 60) / timelimit  # Heart rate in BPM
print(f"Heart Rate = {hbpermin:.2f}")
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
