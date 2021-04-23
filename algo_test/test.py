from music.models import Standard
print(Standard.objects.get(name="Ode To Joy").info["notes"])