import array
import numpy as np
import scipy
from pydub.utils import get_array_type
from scipy.fft import fft
import sys
#sys.path.append("/usr/local/lib/python3.7/site-packages")
sys.path.append("/usr/local/lib/python3.8/site-packages")
import essentia
# import essentia.standard as es
from essentia.standard import *
from pydub import AudioSegment
from music.models import Song, Frequency, Standard

def convert_song_to_array(file_name, segment_ms):
    song = AudioSegment.from_file(file_name)
    print("song length", len(song))
    # Size of segments to break song into for volume calculations
    # SEGMENT_MS = 1
    # dBFS is decibels relative to the maximum possible loudness
    volume = [segment.dBFS for segment in song[::segment_ms]]
    print("volume length",len(volume))
    return song, volume

def detect_bpm(file_name):
    """method 1:
    features, features_frames = MusicExtractor(lowlevelStats=['mean', 'stdev'],
                                               rhythmStats=['mean', 'stdev'],
                                               tonalStats=['mean', 'stdev'])(file_name)
    print("BPM from algorithm: ", features['rhythm.bpm'])
    detected_bpm = features['rhythm.bpm']
    return detected_bpm
    """
    # method 2:
    # Loading audio file
    audio = MonoLoader(filename=file_name)()

    # Compute beat positions and BPM
    rhythm_extractor = RhythmExtractor2013(method="multifeature")
    detected_bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)

    print("BPM:", detected_bpm)
    return detected_bpm
    
    

def detect_onsets(file_name):
    # Loading audio file
    audio = MonoLoader(filename=file_name)()
    # Computing onset detection functions.
    od1 = OnsetDetection(method='hfc')

    w = Windowing(type = 'hann')
    fft = FFT() # this gives us a complex FFT
    c2p = CartesianToPolar() # and this turns it into a pair (magnitude, phase)
    pool = essentia.Pool()

    for frame in FrameGenerator(audio, frameSize = 1024, hopSize = 512):
        mag, phase, = c2p(fft(w(frame)))
        pool.add('features.hfc', od1(mag, phase))

    # compute the actual onsets locations
    onsets = Onsets()

    onsets_hfc = onsets(essentia.array([ pool['features.hfc'] ]), [ 1 ])
    print("number of onsets:", len(onsets_hfc))
    if len(onsets_hfc) > 0:
        print("first onsets: ", onsets_hfc[0])
    else:
        print("no onset")

    return audio, onsets_hfc

def filter_noise(volume, onsets_hfc, i_range, lowest_volume):
    detected_onsets = []
    for s in onsets_hfc:
        s_i = int(s*1000)
        if (volume[s_i] > lowest_volume or
                volume[s_i+i_range]>lowest_volume or
                volume[s_i-i_range]>lowest_volume):
            detected_onsets.append(s*1000)
        else:
            print("deleted onset at: ", s*1000)

    # print(filter_time)
    # print(len(filter_time))
    # print(t_onsets)
    return detected_onsets

def frequency_spectrum(sample, max_frequency=4187):
    # For single note, the highest note frequency = 4186.009 (for 88 keys piano)
    """
    Derive frequency spectrum of a signal pydub.AudioSample
    Returns an array of frequencies and an array of how prevelant that frequency is in the sample
    """
    # Convert pydub.AudioSample to raw audio data
    # Copied from Jiaaro's answer on https://stackoverflow.com/questions/32373996/pydub-raw-audio-data
    bit_depth = sample.sample_width * 8
    array_type = get_array_type(bit_depth)
    raw_audio_data = array.array(array_type, sample._data)
    n = len(raw_audio_data)

    # Compute FFT and frequency value for each index in FFT array
    # Inspired by Reveille's answer on https://stackoverflow.com/questions/53308674/audio-frequencies-in-python
    freq_array = np.arange(n) * (float(sample.frame_rate) / n)  # two sides frequency range
    freq_array = freq_array[: (n // 2)]  # one side frequency range

    raw_audio_data = raw_audio_data - np.average(raw_audio_data)  # zero-centering
    freq_magnitude = fft(raw_audio_data)  # fft computing and normalization
    freq_magnitude = freq_magnitude[: (n // 2)]  # one side

    if max_frequency:
        max_index = int(max_frequency * n / sample.frame_rate) + 1
        freq_array = freq_array[:max_index]
        freq_magnitude = freq_magnitude[:max_index]

    freq_magnitude = abs(freq_magnitude)
    freq_magnitude = freq_magnitude / np.sum(freq_magnitude)

    return freq_array, freq_magnitude

def detect_frequency(song, detected_onsets, detect_onset_before, detect_onset_after):
    detected_freqs = []
    for start in detected_onsets:
        sample_from = int(start + detect_onset_before)
        sample_to = int(start + detect_onset_after)
        segment = song[sample_from:sample_to]
        freqs, freq_magnitudes = frequency_spectrum(segment)
        #     print(freqs[np.argmax(freq_magnitudes)])
        detected_freqs.append(freqs[np.argmax(freq_magnitudes)])
    return detected_freqs
