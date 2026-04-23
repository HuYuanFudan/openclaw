# middleware.py
class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Access-Control-Allow-Origin'] = '*'  # 允许所有域名访问
        # 如果需要指定特定域名，可以这样写：
        # response['Access-Control-Allow-Origin'] = 'https://example.com'
        return response