from django.db import models

class Product(models.Model):
    name            = models.CharField(max_length=100)
    effective_time  = models.DurationField(null=True)
    price           = models.DecimalField(max_digits=10, decimal_places=2)
    sale            = models.DecimalField(max_digits=3, decimal_places=2)
    start_date      = models.DateField()
    thumbnail_image = models.URLField(max_length=1000)
    main_category   = models.ForeignKey('product.MainCategory', on_delete=models.SET_NULL, null=True)
    sub_category    = models.ForeignKey('product.SubCategory', on_delete=models.SET_NULL, null=True)
    difficulty      = models.ForeignKey('product.Difficulty', on_delete=models.SET_NULL, null=True)
    creator         = models.ForeignKey('user.User', on_delete=models.CASCADE, null=True)
    signature       = models.ForeignKey('product.Signature', on_delete=models.CASCADE, null=True)
    kit             = models.ManyToManyField('kit.Kit', through='ProductKit')
    detail_category = models.ManyToManyField('product.DetailCategory', through='ProductDetailCategory')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateField(auto_now=True, editable=True)
    is_deleted      = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'products'

class ProductSubImage(models.Model):
    image_url = models.URLField(max_length=1000)
    product   = models.ForeignKey('product.Product', on_delete=models.CASCADE)

    class Meta:
        db_table = 'product_sub_images'

class ProductContentImageUrl(models.Model):
    image_url = models.URLField(max_length=1000)

    class Meta:
        db_table = 'product_content_image_urls'

class ProductContentDescription(models.Model):
    description = models.CharField(max_length=1000)

    class Meta:
        db_table = 'product_content_descriptions'

class ProductContent(models.Model):
    image_url   = models.ForeignKey('product.ProductContentImageUrl', on_delete=models.SET_NULL, null=True)
    description = models.ForeignKey('product.ProductContentDescription', on_delete=models.SET_NULL, null=True)
    order       = models.IntegerField()

    class Meta:
        db_table = 'product_contents'

class Community(models.Model):
    description = models.CharField(max_length=1000)
    user        = models.ForeignKey('user.User', on_delete=models.CASCADE)
    product     = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True, editable=True)
    
    class Meta:
        db_table = 'communities'

class CommunityComment(models.Model):
    content    = models.CharField(max_length=500)
    user       = models.ForeignKey('user.User', on_delete=models.CASCADE)
    community  = models.ForeignKey('product.Community', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, editable=True)
    
    class Meta:
        db_table = 'community_comments'

class CommunityLike(models.Model):
    user      = models.ForeignKey('user.User', on_delete=models.CASCADE)
    community = models.ForeignKey('product.Community', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'community_likes'

class MainCategory(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'main_categories'

class SubCategory(models.Model):
    name          = models.CharField(max_length=50)
    main_category = models.ForeignKey('product.MainCategory', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table ='sub_categories'

class Difficulty(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        db_table = 'difficulties'

class DetailCategory(models.Model):
    name = models.CharField(max_length=40)

    class Meta:
        db_table = 'detail_categories'

class ProductDetailCategory(models.Model):
    product         = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    detail_category = models.ForeignKey('product.DetailCategory', on_delete=models.CASCADE)

    class Meta:
        db_table = 'products_detail_categories'
    
class Chapter(models.Model):
    name            = models.CharField(max_length=100)
    product         = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    order           = models.IntegerField()
    thumbnail_image = models.URLField(max_length=1000)

    class Meta:
        db_table = 'chapters'

class Lecture(models.Model):
    name      = models.CharField(max_length=40)
    product   = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    video     = models.OneToOneField('product.LectureVideo', on_delete=models.SET_NULL, null=True)
    chapter   = models.ForeignKey('product.Chapter', on_delete=models.SET_NULL, null=True)
    order     = models.IntegerField()

    class Meta:
        db_table = 'lectures'

class LectureVideo(models.Model):
    video_url = models.URLField(max_length=1000, null=True)
    duration = models.DurationField(null=True)
    
    class Meta:
        db_table = 'lecture_videos'

class LectureComment(models.Model):
    content    = models.CharField(max_length=200)
    image_url  = models.URLField(max_length=1000, null=True)
    user       = models.ForeignKey('user.User', on_delete=models.CASCADE)
    parent     = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    lecture    = models.ForeignKey('product.Lecture', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, editable=True)

    class Meta:
        db_table = 'lecture_comments'

class LectureContentDescription(models.Model):
    description = models.CharField(max_length=1000)

    class Meta:
        db_table = 'lecture_content_descriptions'

class LectureContentImageUrl(models.Model):
    image_url = models.URLField(max_length=1000)

    class Meta:
        db_table = 'lecture_content_image_urls'

class LectureContent(models.Model):
    description = models.ForeignKey('product.LectureContentDescription', on_delete=models.SET_NULL, null=True)
    image_url   = models.ForeignKey('product.LectureContentImageUrl', on_delete=models.SET_NULL, null=True)
    lecture     = models.ForeignKey('product.Lecture', on_delete=models.CASCADE)
    product     = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    order       = models.IntegerField()

    class Meta:
        db_table = 'lecture_contents'

class LectureProgress(models.Model):
    user       = models.ForeignKey('user.User', on_delete=models.CASCADE)
    product    = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    lecture    = models.ForeignKey('product.Lecture', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, editable=True)

    class Meta:
        db_table = 'lecture_progresses'

class Signature(models.Model):
    name = models.CharField(max_length=40)

    class Meta:
        db_table = 'signatures'

class ProductKit(models.Model):
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    kit     = models.ForeignKey('kit.Kit', on_delete=models.CASCADE)

    class Meta:
        db_table = 'products_kits'

