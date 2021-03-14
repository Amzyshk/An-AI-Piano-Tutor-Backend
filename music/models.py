from django.db import models


class Song(models.Model):
    name = models.CharField(max_length=200)
    audio = models.FileField(upload_to='audios')
    pic = models.ImageField(upload_to='pics')

#    def __str__(self):
#        return self.name

