from music.models import Song, Frequency, Standard
from .print_tool import *

def get_standard_detect_time_slot(song_name, standard_onsets, total_num, slot_range):
    # total_num = 62
    #this is time slices for splitting notes
    split_time = []
    note_duration = Standard.objects.get(name=song_name).info["note_duration"]
    split_time.append((standard_onsets[0]- 0.5*slot_range, standard_onsets[0]+0.5*note_duration[0]*slot_range))
    for i in range(1, total_num-1):
        min_time = standard_onsets[i]-0.5*note_duration[i-1]*slot_range
        max_time = standard_onsets[i]+0.5*note_duration[i]*slot_range
        split_time.append((min_time, max_time))
    #change: the last one note duration
    split_time.append((standard_onsets[total_num-1]-0.5*note_duration[total_num-2]*slot_range,
                       standard_onsets[total_num-1]+0.5*note_duration[total_num-1]*slot_range))
    #print(len(split_time))
    return split_time


def get_detected_onset_freq_pair(song_name, standard_onsets, total_num, detected_onsets, detected_freqs, slot_range):
    #each pair is a list of time, a list of freq for examine at a standard onset
    examine_freqs = []
    for i in range(0, total_num):
        examine_freqs.append(([],[]))

    split_time = get_standard_detect_time_slot(song_name, standard_onsets, total_num, slot_range)

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

    return examine_freqs


def get_compare_result(song_name,
                       standard_onsets, standard_freqs,
                       detected_onsets, detected_freqs,
                       total_num, slot_range,
                       dup_time_tol, beat_error_tol, freq_error_tol):
    examine_freqs = get_detected_onset_freq_pair(song_name,standard_onsets, total_num, detected_onsets, detected_freqs, slot_range)
    result = ["False"]*total_num
    correct_count = 0
    freq_error_count = 0
    beat_error_count = 0
    for i in range(0, total_num):
        examine_t = examine_freqs[i][0]
        examine_f = examine_freqs[i][1]
        standard_t = standard_onsets[i]
        standard_f = standard_freqs[i]
        min_freq = standard_f - freq_error_tol
        max_freq = standard_f + freq_error_tol
        min_time = standard_t - beat_error_tol
        max_time = standard_t + beat_error_tol
        detected_num = len(examine_f)
        if detected_num > 1: # play more notes
            #see whether duplicate
            max_time_diff = 0
            for n in range(1, detected_num):
                time_diff = examine_t[n]-examine_t[n-1]
                if time_diff>max_time_diff:
                    max_time_diff = time_diff
            
            if max_time_diff <= dup_time_tol:#regard as algorithm error, still considered as one note
                #result[i] = "True"
                #correct_count += 1
                beat = False
                note = False
                for x in range(0, detected_num):
                    if ((examine_t[x] >= min_time) and (examine_t[x] <= max_time)):#regard as correct beat
                        beat = True
                    if ((examine_f[x] >= min_freq) and (examine_f[x] <= max_freq)):#correct freq
                        note = True
                
                if (beat == True) and (note == True):
                    result[i] = "True"
                    correct_count += 1
                elif (beat == True) and (note == False):
                    result[i] = "WrongFreq"
                    freq_error_count += 1
                elif (beat == False) and (note == True):
                    result[i] = "WrongBeat"
                    beat_error_count += 1
                else:
                    result[i] = "Wrong"
                    freq_error_count += 1
                    beat_error_count += 1

            else:#really extra notes played
                result[i] = "Dup"
                #regard as beat wrong and freq wrong
                beat_error_count += 1
                freq_error_count += 1

        elif detected_num < 1: # miss the note
            result[i] = "Miss"
            #beat wrong and freq wrong
            beat_error_count += 1
            freq_error_count += 1
        else:#only one note, see freq
            if ((examine_t[0] >= min_time) and (examine_t[0] <= max_time)):#regard as correct beat
                if ((examine_f[0] >= min_freq) and (examine_f[0] <= max_freq)):#correct freq
                    result[i] = "True"
                    correct_count += 1
                else:#wrong freq but correct beat
                    result[i] = "WrongFreq"
                    freq_error_count += 1
            else:# wrong beat
                if ((examine_f[0] >= min_freq) and (examine_f[0] <= max_freq)):#wrong beat but correct freq
                    result[i] = "WrongBeat"
                    beat_error_count += 1
                else:#wrong beat and wrong freq
                    result[i] = "Wrong"
                    freq_error_count += 1
                    beat_error_count += 1

    pretty_print_result(song_name, result, total_num)
    print("correct_count:", correct_count)
    print("freq_error", freq_error_count)
    print("beat_error", beat_error_count)
    return result, correct_count, freq_error_count, beat_error_count

def get_overall_result(total_num, correct_count, freq_error_count, beat_error_count, bpm, detected_bpm):
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

    return overall_report