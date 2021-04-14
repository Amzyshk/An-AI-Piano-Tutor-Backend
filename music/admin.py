from django.contrib import admin

from .models import Song, Frequency, Standard

admin.site.register(Song)
admin.site.register(Frequency)
admin.site.register(Standard)