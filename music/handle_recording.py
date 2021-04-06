def handle_recording(f):
    with open('media/audios/recording.m4a', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)