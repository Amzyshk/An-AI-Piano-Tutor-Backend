import time


def handle_recording(f):
    name = str(int(time.time()))
    path = 'media/audios/' + name + '.m4a'
    with open(path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
