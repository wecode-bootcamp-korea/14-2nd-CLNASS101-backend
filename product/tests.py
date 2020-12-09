import json
from datetime       import date, timedelta

from django.test    import Client, TransactionTestCase
from django.urls    import reverse
from django.db      import connection

from product.models import (
    Product,
    ProductSubImage,
    MainCategory,
    SubCategory,
    Difficulty,
    Chapter,
    Community,
    Signature
)

from user.models    import User
from kit.models     import Kit

class TestProductDetailView(TransactionTestCase):
    
    @classmethod
    def setUpTestData(cls):
        pass
    
    def setUp(self):
        self.client = Client()
        pass
