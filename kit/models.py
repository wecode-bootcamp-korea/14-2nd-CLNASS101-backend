from django.db import models

class Kit(models.Model):
    name           = models.CharField(max_length=100, null=True)
    main_image_url = models.URLField(max_length=1000)
    price          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description    = models.CharField(max_length=1000, null=True)

    class Meta:
        db_table = 'kits'

class KitSubImageUrl(models.Model):
    image_url = models.URLField(max_length=1000)
    kit       = models.ForeignKey('kit.Kit', on_delete=models.CASCADE)

    class Meta:
        db_table = 'kit_sub_image_urls'

class KitLike(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    kit  = models.ForeignKey('kit.Kit', on_delete=models.CASCADE)

    class Meta:
        db_table = 'kit_likes'
