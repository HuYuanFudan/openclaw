# your_app/decorators.py
from django.http import HttpResponseForbidden
def neo4j_user_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'neo4j':
            return HttpResponseForbidden("You are not authorized to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
def metaknowledge_user_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'metaknowledge':
            return HttpResponseForbidden("You are not authorized to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

