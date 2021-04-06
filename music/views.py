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
        # Store the uploaded recording at /media/audios
        handle_recording(request.FILES['recording'])
        # TODO: Please process the recording here and return in the following format:
        # TODO: an array of the index of the error notes
        # TODO: Please remember to delete that recording file after processing.
        response = JsonResponse([3, 4], safe=False)
        return HttpResponse(response, content_type='application/json')
    return HttpResponse("Something wrong", content_type="text/plain")
