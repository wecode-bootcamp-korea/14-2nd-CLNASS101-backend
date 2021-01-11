from django.db import models

class TemporaryProduct(models.Model):
    main_category = models.ForeignKey('product.MainCategory', on_delete=models.SET_NULL, null=True)
    sub_category  = models.ForeignKey('product.SubCategory', on_delete=models.SET_NULL, null=True)
    name          = models.CharField(max_length=100)
    price         = models.IntegerField()
    sale          = models.DecimalField(max_digits=3, decimal_places=2)
    difficulty    = models.ForeignKey('product.Difficulty', on_delete=models.SET_NULL, null=True)
    user          = models.ForeignKey('user.User', on_delete=models.CASCADE)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True, editable=True)

    class Meta:
        db_table = 'temporary_products'

class TemporaryProductImage(models.Model):
    image_url         = models.URLField(max_length=200)
    temporary_product = models.ForeignKey('creator.TemporaryProduct', on_delete=models.CASCADE)

    class Meta:
        db_table = 'temporary_product_images'

class TemporaryChapter(models.Model):
    name              = models.CharField(max_length=100)
    thumbnail_image   = models.URLField(max_length=200, null=True)
    temporary_product = models.ForeignKey('creator.TemporaryProduct', on_delete=models.CASCADE)
    order             = models.IntegerField()

    class Meta:
        db_table = 'temporary_chapters'

class TemporaryLecture(models.Model):
    name              = models.CharField(max_length=100)
    video_url         = models.URLField(max_length=200, null=True)
    duration          = models.DurationField(null=True)
    temporary_chapter = models.ForeignKey('creator.TemporaryChapter', on_delete=models.CASCADE)
    temporary_product = models.ForeignKey('creator.TemporaryProduct', on_delete=models.CASCADE)
    order             = models.IntegerField()

    class Meta:
        db_table = 'temporary_lectures'

class TemporaryLectureContentImage(models.Model):
    image_url = models.CharField(max_length=200)
    temporary_lecture = models.ForeignKey('creator.TemporaryLecture', on_delete=models.CASCADE)
    temporary_product = models.ForeignKey('creator.TemporaryProduct', on_delete=models.CASCADE)

    class Meta:
        db_table = 'temporary_lecture_content_images'

class TemporaryLectureContentDescription(models.Model):
    description = models.CharField(max_length=500)
    temporary_lecture = models.ForeignKey('creator.TemporaryLecture', on_delete=models.CASCADE)
    temporary_product = models.ForeignKey('creator.TemporaryProduct', on_delete=models.CASCADE)


    class Meta:
        db_table = 'temporary_lecture_content_descriptions'

class TemporaryLectureContent(models.Model):
    image             = models.ForeignKey('creator.TemporaryLectureContentImage', on_delete=models.SET_NULL, null=True)
    description       = models.ForeignKey('creator.TemporaryLectureContentDescription', on_delete=models.SET_NULL, null=True)
    temporary_lecture = models.ForeignKey('creator.TemporaryLecture', on_delete=models.CASCADE)
    temporary_product = models.ForeignKey('creator.TemporaryProduct', on_delete=models.CASCADE)
    order             = models.IntegerField()

    class Meta:
        db_table = 'temporary_lecture_contents'

class TemporaryKit(models.Model):
    name              = models.CharField(max_length=100)
    price             = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    temporary_product = models.ForeignKey('creator.TemporaryProduct', on_delete=models.CASCADE)

    class Meta:
        db_table = 'temporary_kits'

class TemporaryKitImage(models.Model):
    image_url         = models.URLField(max_length=200)
    temporary_kit     = models.ForeignKey('creator.TemporaryKit', on_delete=models.CASCADE)
    temporary_product = models.ForeignKey('creator.TemporaryProduct', on_delete=models.CASCADE)

    class Meta:
        db_table = 'temporary_kit_images'
