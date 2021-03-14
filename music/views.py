from django.http import HttpResponse
from music.models import Song


def index(request):
    return HttpResponse("Hello, world. You're at the music index.")


def songs(request):
    response = Song.objects.all()
    return HttpResponse(response)
