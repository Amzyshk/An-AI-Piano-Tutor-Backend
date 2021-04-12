from django.http import HttpResponse
from django.http import JsonResponse
from music.models import Song
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from .handle_recording import handle_recording


def index(request):
    return HttpResponse("Hello, world. You're at the music index.")


def songs(request):
    data = Song.objects.all()
    data_json = serializers.serialize('json', data)
    return HttpResponse(data_json, content_type='application/json')


@csrf_exempt
def upload(request):
    if request.method == 'POST':
        # This is the starting time of the first note calculated at the front-end
        start_time = float(request.POST['start_time'])
        # This is the selected BPM
        bpm = float(request.POST['bpm'])
        print("-------------start_time received: ", start_time)
        # Store the uploaded recording at /media/audios
        handle_recording(request.FILES['recording'])
        # TODO: Please process the recording here and return in the following format:
        # TODO: an array of 0 or 1, where 0 indicates the note is correct, 1 indicates it has wrong frequency,
        # TODO: 2 indicates it's omitted, 3 indicates 多弹, 4 indicates it has wrong rhythm
        # TODO: the length of the array should be the total number of notes in the piece, 62 for Ode to Joy.
        data = []
        for i in range(62):
            if i == 2:
                data.append(2)
            elif i == 5:
                data.append(3)
            elif i == 10:
                data.append(4)
            else:
                data.append(1)
        res = {'bpm': 120, 'speed': 0.8, 'note': 0.9, 'rhythm': 0.7, 'overall': 0.9, 'data': data}
        response = JsonResponse(res, safe=False)
        return HttpResponse(response, content_type='application/json')
    return HttpResponse("Something wrong", content_type="text/plain")
