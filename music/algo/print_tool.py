from music.models import Song, Frequency, Standard

def print_function_running(msg):
    print("="*10 + " " + msg + " " + "="*10)

def pretty_print_result(song_name, result, total_num):
    pretty_res = ""
    notes = Standard.objects.get(name=song_name).info["notes"]
    for i in range(0, total_num):
        pretty_res += (notes[i]+":"+result[i]+" | ")
    print(pretty_res)
