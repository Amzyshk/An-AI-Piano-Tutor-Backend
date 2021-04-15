import numpy as np
import sys
#sys.path.append("/usr/local/lib/python3.7/site-packages")
sys.path.append("/usr/local/lib/python3.8/site-packages")
from pylab import plot, show, figure, imshow
import matplotlib.pyplot as plt

def plt_hfc_onsets(audio, onsets_hfc):
    plt.rcParams['figure.figsize'] = (18, 6) # set plot sizes to something larger than default
    plot(audio)
    for onset in onsets_hfc:
        plt.axvline(x=onset*44100, color='red')
    plt.title("Audio waveform and the estimated onset positions (HFC onset detection function)")
    plt.show()

def plt_onsets_after_breaking(volume, onsets_hfc):
    plt.rcParams['figure.figsize'] = (18, 6) # set plot sizes to something larger than default
    x_axis = np.arange(len(volume))
    plt.plot(x_axis, volume)
    for s in onsets_hfc:
        plt.axvline(x=s*1000, color='r', linewidth=0.5, linestyle="-")
    plt.show()


def plt_standard_detected_onsets_freqs(standard_onsets, detected_onsets, standard_freqs, detected_freqs):
    plt.rcParams['figure.figsize'] = (18, 6) # set plot sizes to something larger than default
    for x in standard_onsets:
        plt.axvline(x=x, color='g', linewidth=0.5, linestyle="-")

    for x in detected_onsets:
        plt.axvline(x=x, color='r', linewidth=0.5, linestyle="-")

    plt.plot(detected_onsets, detected_freqs)
    plt.plot(standard_onsets, standard_freqs)
    plt.show()
