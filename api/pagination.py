from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPagination(PageNumberPagination):
    page_size = 10 # Default page size
    page_size_query_param = 'page_size' # Allow client to override, using `?page_size=xxx`
    max_page_size = 100 # Maximum limit allowed when using `page_size` query param

    def get_paginated_response(self, data):
        return Response({
            'status': 'success',
            'message': 'Data fetched successfully',
            'meta': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'data': data
        })
