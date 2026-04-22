from django.db import models
from django.contrib.auth.models import User
from PIL import Image
import os
from django.conf import settings
# Create your models here.

# Función para guardar la imagen del perfil del usuario
def save_profile_image(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f'user_{instance.user.id}{ext}'
    return os.path.join('profile_images', filename)

# Modelo para el perfil del usuario
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to= save_profile_image, null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    # Redimensionar la imagen del perfil del usuario
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            img = Image.open(self.image.path)

            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.image.path)