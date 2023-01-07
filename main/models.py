from django.db import models
# Create your models here.
class MyModel(models.Model):
  
    # file will be uploaded to MEDIA_ROOT / uploads
    upload = models.ImageField(upload_to= "uploads/",blank=True,null=True)