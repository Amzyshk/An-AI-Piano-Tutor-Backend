import sys
#sys.path.append("/usr/local/lib/python3.7/site-packages")
sys.path.append("/usr/local/lib/python3.8/site-packages")
import essentia
from essentia.standard import *
from music.models import Song, Frequency, Standard
from .process_music_methods import *
from .print_tool import *
from .compare_methods import get_compare_result, get_overall_result
from .plt_methods import plt_hfc_onsets, plt_onsets_after_breaking, plt_standard_detected_onsets_freqs


def get_audio_start_time(detected_onsets):
    # in ms
    return detected_onsets[1]


def get_bpm():
    return 119


def get_bt_ms():
    bpm = get_bpm()
    bt = 60 / bpm
    bt_ms = bt * 1000
    return bt_ms


def get_standard_song_info(song_name, audio_start_time):
    notes = Standard.objects.get(name=song_name).info["notes"]
    total_num = len(notes)
    standard_freqs = []
    for note in notes:
        standard_freqs.append(Frequency.objects.get(note=note).freq)

    bt_ms = get_bt_ms()
    beat_index = Standard.objects.get(name=song_name).info["beat_index"]
    standard_onsets = []
    #in ms
    for i in beat_index:
        standard_onsets.append(audio_start_time + i*bt_ms)

    return standard_onsets, standard_freqs, total_num


#file = "../algo_wxm/audio/longwrongE4.m4a"
def process_music(file_name, start_time, bpm, song_name):

    print_function_running("converting song to array")
    song, volume = convert_song_to_array(file_name, segment_ms=1)

    print_function_running("detecting onset")
    audio, onsets_hfc = detect_onsets(file_name)
    # plt_hfc_onsets(audio ,onsets_hfc)
    # plt_onsets_after_breaking(volume, onsets_hfc)

    print_function_running("filtering noise")
    LOWEST_VOLUME = -40
    VOLUME_RANGE = 5
    detected_onsets = filter_noise(volume, onsets_hfc, VOLUME_RANGE, LOWEST_VOLUME)

    print_function_running("checking if onsets exist")
    if len(detected_onsets) <= 2:
        return [], {}

    print_function_running("detecting bpm")
    detected_bpm = detect_bpm(file_name)

    print_function_running("detecting frequency")
    DETECT_ONSET_BEFORE = 0
    DETECT_ONSET_AFTER = 200
    detected_freqs = detect_frequency(song, detected_onsets, DETECT_ONSET_BEFORE, DETECT_ONSET_AFTER)

    '''
    get the input audio start time, and apply to standard onsets
    '''
    audio_start_time = get_audio_start_time(detected_onsets)
    standard_onsets, standard_freqs, total_num = get_standard_song_info(song_name, audio_start_time)
    # plt_standard_detected_onsets_freqs(standard_onsets, detected_onsets, standard_freqs, detected_freqs)

    print_function_running("comparing")
    #error tolerance of frequency
    freq_error_tol = 5
    #for duplicate onsets, maybe because of onset detect error, permit a small time diff as only one note
    dup_time_tol = 150
    #for beat time error tolerance
    beat_error_tol = 150
    slot_range = get_bt_ms()
    result, correct_count, freq_error_count, beat_error_count = get_compare_result(song_name,
                                 standard_onsets, standard_freqs,
                                 detected_onsets, detected_freqs,
                                 total_num, slot_range,
                                 dup_time_tol, beat_error_tol, freq_error_tol)

    print_function_running("generating overall report")
    bpm = get_bpm()
    overall_report = get_overall_result(total_num, correct_count, freq_error_count, beat_error_count, bpm, detected_bpm)

    return result, overall_report
                    



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

    """
    detected_onsets = [-10, 0, 9, 10, 31, 42, 56, 57.5, 60, 80, 90]
    detected_freqs = [10, 1, 2, 2, 4, 5, 6, 6, 7, 8, 10]
    standard_onsets = [0, 10, 20, 30, 40, 55, 60, 80]
    standard_freqs = [1, 2, 3, 4, 5, 6, 7, 8]
    total_num = 8
    note_duration = [1, 1, 1, 1, 1.5, 0.5, 2, 1]
    bt_ms = 10
    """
