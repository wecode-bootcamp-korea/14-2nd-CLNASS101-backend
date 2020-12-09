import json
from datetime       import date

from django.views   import View
from django.http    import JsonResponse

from product.models import Product
from user.models    import User, ProductLike, RecentlyView
from core.utils     import login_decorator

import time
import functools
from django.db      import connection, reset_queries

def query_debugger(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        number_of_start_queries = len(connection.queries)
        start  = time.perf_counter()
        result = func(*args, **kwargs)
        end    = time.perf_counter()
        number_of_end_queries = len(connection.queries)
        print(f"-------------------------------------------------------------------")
        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {number_of_end_queries-number_of_start_queries}")
        print(f"Finished in : {(end - start):.2f}s")
        print(f"-------------------------------------------------------------------")
        return result
    return wrapper

class ClassDetailView(View):
    @query_debugger
    @login_decorator(view_name='ClassDetailView')
    def get(self, request, product_id):
        try:
            if not isinstance(product_id, int):
                raise TypeError
            pass
            
        except TypeError:
            return JsonResponse({'MESSAGE': 'TYPE_ERROR'}, status=400)
        
        return JsonResponse({'MESSAGE': 'SUCCESS'}, status=200)