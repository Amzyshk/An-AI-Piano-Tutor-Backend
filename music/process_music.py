import array
import numpy as np
import json
import scipy
from pydub.utils import get_array_type
from scipy.fft import fft
import sys
#sys.path.append("/usr/local/lib/python3.7/site-packages")
sys.path.append("/usr/local/lib/python3.8/site-packages")
import essentia
# import essentia.standard as es
from essentia.standard import *
#%matplotlib inline
#import matplotlib.pyplot as plt
#plt.rcParams['figure.figsize'] = (15, 6) # set plot sizes to something larger than default
from pydub import AudioSegment

from music.models import Song, Frequency, Standard

#file = "../algo_wxm/audio/longwrongE4.m4a"

def process_music(fileName, start_time, bpm):
    MUSIC = "Ode To Joy"
    def frequency_spectrum(sample, max_frequency=4187):
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

    
    # Compute all features, aggregate only 'mean' and 'stdev' statistics for all low-level, rhythm and tonal frame features
    features, features_frames = MusicExtractor(lowlevelStats=['mean', 'stdev'], 
                                              rhythmStats=['mean', 'stdev'], 
                                              tonalStats=['mean', 'stdev'])(fileName)
    print("BPM:", features['rhythm.bpm'])
    detected_bpm = features['rhythm.bpm']
    
    


    #ONSET DETECTION


    # Loading audio file
    audio = MonoLoader(filename=fileName)()
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

    """
    plot(audio)
    for onset in onsets_hfc:
        plt.axvline(x=onset*44100, color='red')
    plt.title("Audio waveform and the estimated onset positions (HFC onset detection function)")
    plt.show()
    """    
    print("number of onsets:", len(onsets_hfc))
    #print(onsets_hfc)

    


    #FILTER NOISE

    song = AudioSegment.from_file(fileName)
    print("song length", len(song))
    # Size of segments to break song into for volume calculations
    SEGMENT_MS = 1
    # dBFS is decibels relative to the maximum possible loudness
    volume = [segment.dBFS for segment in song[::SEGMENT_MS]]
    print("volume length",len(volume))

    """
    plt.rcParams['figure.figsize'] = (18, 6) # set plot sizes to something larger than default
    x_axis = np.arange(len(volume))
    plt.plot(x_axis, volume)
    for s in onsets_hfc:
        plt.axvline(x=s*1000, color='r', linewidth=0.5, linestyle="-")
    plt.show()
    """

    filter_time = []
    i_range = 5
    lowest_volume = -40
    for s in onsets_hfc:
        s_i = int(s*1000)
        if (volume[s_i] > lowest_volume or 
            volume[s_i+i_range]>lowest_volume or 
            volume[s_i-i_range]>lowest_volume):
            filter_time.append(s*1000)
        else:
            print(s*1000)
            
    # print(filter_time)
    # print(len(filter_time))
    detected_onsets = filter_time
    # print(t_onsets)


    #STANDARD OF MUSIC

    # c4 = 261.626
    # d4 = 293.665
    # e4 = 329.629
    # f4 = 349.228
    # g4 = 391.995
    # g3 = 195.998
    # standard_freqs = [e4,e4,f4,g4,
    #         g4,f4,e4,d4,
    #         c4,c4,d4,e4,
    #         e4,d4,d4,
    #         e4,e4,f4,g4,
    #         g4,f4,e4,d4,
    #         c4,c4,d4,e4,
    #         d4,c4,c4,
    #         d4,d4,e4,c4,
    #         d4,e4,f4,e4,c4,
    #         d4,e4,f4,e4,d4,
    #         c4,d4,g3,
    #         e4,e4,f4,g4,
    #         g4,f4,e4,d4,
    #         c4,c4,d4,e4,
    #         d4,c4,c4]
    #print(len(standard_freqs))
    notes = Standard.objects.get(name=MUSIC).info["notes"]
    standard_freqs = []
    for note in notes:
        standard_freqs.append(Frequency.objects.get(note=note).freq)

    # beat_index = [0,1,2,3,
    #             4,5,6,7,
    #             8,9,10,11,
    #             12,13.5,14,
    #             16,17,18,19,
    #             20,21,22,23,
    #             24,25,26,27,
    #             28,29.5,30,
    #             32,33,34,35,
    #             36,37,37.5,38,39,
    #             40,41,41.5,42,43,
    #             44,45,46,
    #             48,49,50,51,
    #             52,53,54,55,
    #             56,57,58,59,
    #             60,61.5,62]
    beat_index = Standard.objects.get(name=MUSIC).info["beat_index"]

    note_duration = Standard.objects.get(name=MUSIC).info["note_duration"]
    # note_duration = [1, 1, 1, 1,
    #                 1, 1, 1, 1,
    #                 1, 1, 1, 1,
    #                 1.5, 0.5, 2,
    #                 1, 1, 1, 1,
    #                 1, 1, 1, 1,
    #                 1, 1, 1, 1,
    #                 1.5, 0.5, 2,
    #                 1, 1, 1, 1,
    #                 1, 0.5, 0.5, 1, 1,
    #                 1, 0.5, 0.5, 1, 1,
    #                 1, 1, 2,
    #                 1, 1, 1, 1,
    #                 1, 1, 1, 1,
    #                 1, 1, 1, 1,
    #                 1.5, 0.5, 2]
    #print(sum(note_duration))

    bpm = 119
    bt = 60 / bpm
    bt_ms = bt*1000
    audio_start_time = detected_onsets[1]

    standard_onsets = []
    #in ms
    for i in beat_index:
        standard_onsets.append(audio_start_time + i*bt*1000)
        
    #print(len(standard_onsets))


    #FREQUENCY DETECTION


    detected_freqs = []
    for start in detected_onsets:
        sample_from = int(start)
        sample_to = int(start + 200)
        segment = song[sample_from:sample_to]
        freqs, freq_magnitudes = frequency_spectrum(segment)
    #     print(freqs[np.argmax(freq_magnitudes)])
        detected_freqs.append(freqs[np.argmax(freq_magnitudes)])
    """    
    # x_axis = np.arange(len(volume)) * (SEGMENT_MS / 1000)
    for x in standard_onsets:
        plt.axvline(x=x, color='g', linewidth=0.5, linestyle="-")
        
    for x in detected_onsets:
        plt.axvline(x=x, color='r', linewidth=0.5, linestyle="-")
        
    plt.plot(detected_onsets, detected_freqs)
    print(detected_onsets)

    plt.plot(standard_onsets, standard_freqs)
    """

    # notes = ["E4","E4","F4","G4",
    #        "G4","F4","E4","D4",
    #        "C4","C4","D4","E4",
    #        "E4","D4","D4",
    #        "E4","E4","F4","G4",
    #        "G4","F4","E4","D4",
    #        "C4","C4","D4","E4",
    #        "D4","C4","C4",
    #        "D4","D4","E4","C4",
    #        "D4","E4","F4","E4","C4",
    #        "D4","E4","F4","E4","D4",
    #        "C4","D4","G3",
    #        "E4","E4","F4","G4",
    #        "G4","F4","E4","D4",
    #        "C4","C4","D4","E4",
    #        "D4","C4","C4"]
    def pretty_print(result, total_num):
        pretty_res = ""
        for i in range(0, total_num):
            pretty_res += (notes[i]+":"+result[i]+" | ")
        print(pretty_res)
    
    """
    detected_onsets = [-10, 0, 9, 10, 31, 42, 56, 57.5, 60, 80, 90]
    detected_freqs = [10, 1, 2, 2, 4, 5, 6, 6, 7, 8, 10]
    standard_onsets = [0, 10, 20, 30, 40, 55, 60, 80]
    standard_freqs = [1, 2, 3, 4, 5, 6, 7, 8]
    total_num = 8
    note_duration = [1, 1, 1, 1, 1.5, 0.5, 2, 1]
    bt_ms = 10
    """

    total_num = 62
    #this is time slices for splitting notes 
    split_time = []
    split_time.append((standard_onsets[0]- 0.5*bt_ms, standard_onsets[0]+0.5*note_duration[0]*bt_ms))
    for i in range(1, total_num-1):
        min_time = standard_onsets[i]-0.5*note_duration[i-1]*bt_ms
        max_time = standard_onsets[i]+0.5*note_duration[i]*bt_ms
        split_time.append((min_time, max_time))
    #change: the last one note duration
    split_time.append((standard_onsets[total_num-1]-0.5*note_duration[total_num-2]*bt_ms, 
                    standard_onsets[total_num-1]+0.5*note_duration[total_num-1]*bt_ms))
    #print(len(split_time))


    #each pair is a list of time, a list of freq for examine at a standard onset
    examine_freqs = []
    for i in range(0, total_num):
        examine_freqs.append(([],[]))

    #separate the onsets into their positions
    cur_onset = 0
    for i in range(0, total_num):
        min_time = split_time[i][0]
        max_time = split_time[i][1]
        for j in range(cur_onset, len(detected_onsets)):
            t = detected_onsets[j]
            freq = detected_freqs[j]
            if (t<min_time):#before the first time slice, very beginning, pass
                cur_onset += 1
                continue
            elif (t>max_time):
                if (i==total_num-1):#final time slice, if >max time, pass all remaining onsets
                    break
                else: #normal case, should stop and go to next time slice
                    break
            else: #fall right into the slice
                (examine_freqs[i])[0].append(t)
                (examine_freqs[i])[1].append(freq)
                cur_onset += 1
                
    #print(examine_freqs)

    result = ["False"]*total_num
    #error tolerance of frequency
    error_tol = 5
    #for duplicate onsets, maybe because of onset detect error, permit a small time diff as only one note
    dup_time_tol = 150
    #for beat time error tolerance
    beat_error_tol = 150
    correct_count = 0
    freq_error_count = 0
    beat_error_count = 0
    for i in range(0, total_num):
        examine_t = examine_freqs[i][0]
        examine_f = examine_freqs[i][1]
        standard_t = standard_onsets[i]
        standard_f = standard_freqs[i]
        min_freq = standard_f - error_tol
        max_freq = standard_f + error_tol
        min_time = standard_t - beat_error_tol
        max_time = standard_t + beat_error_tol
        detected_num = len(examine_f)
        if detected_num > 1: # play more notes 
            max_time_diff = 0
            for n in range(1, detected_num):
                time_diff = examine_t[n]-examine_t[n-1]
                if time_diff>max_time_diff:
                    max_time_diff = time_diff
            if max_time_diff <= dup_time_tol:
                result[i] = "True"
                correct_count += 1
            else:
                result[i] = "Dup"
                beat_error_count += 1
        elif detected_num < 1: # miss the note
            result[i] = "Miss"
        else:#only one note, see freq
            if ((examine_t[0] >= min_time) and (examine_t[0] <= max_time)):#regard as correct beat
                if ((examine_f[0] >= min_freq) and (examine_f[0] <= max_freq)):#correct freq
                    result[i] = "True"
                    correct_count += 1
                else:
                    result[i] = "WrongFreq"
                    freq_error_count += 1
            else:
                result[i] = "WrongBeat"
                beat_error_count += 1
    pretty_print(result, total_num)
    print("correct_count:", correct_count)
    print("freq_error", freq_error_count)
    print("beat_error", beat_error_count)
    print("detected bpm", detected_bpm)

    #overall report, a dictionary
    overall_report = {}
    #frequency accuracy: percentage
    freq_accuracy = (total_num - freq_error_count)/total_num
    freq_score = int(freq_accuracy*100)
    overall_report["freq_accuracy"] = freq_accuracy
    overall_report["freq_score"] = freq_score
    print("freq_score",freq_score)
    #beat accuracy: percentage, take into account:dup and wrongbeat
    beat_accuracy = (total_num - beat_error_count)/total_num
    beat_score = int(beat_accuracy*100)
    overall_report["beat_accuracy"] = beat_accuracy
    overall_report["beat_score"] = beat_score
    print("beat_score", beat_score)
    #speed: 
    speed = detected_bpm
    speed_score = int((1-(abs(bpm - detected_bpm)/bpm))*100)
    overall_report["speed"] = speed
    overall_report["speed_score"] = 1-(abs(bpm - detected_bpm)/bpm)
    print("speed_score", speed_score)
    # correctness: percentage
    correctness = correct_count/total_num
    correctness_score = int(correctness*100)
    overall_report["correctness"] = correctness
    overall_report["correctness_score"] = correctness_score
    print("correctness_score", correctness_score)


    return result, overall_report
                    
        
        
#process_music(file)
