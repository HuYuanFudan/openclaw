"""knowledgegraph URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from .views import MyTokenObtainPairView, AddNodeView, DeleteNodeView, AddNodeExcelView, AddRelationshipExcelView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'allmetaknowledge', views.MetaKnowledgeViewSet, basename='allmetaknowledge')

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('addnode/', AddNodeView.as_view(), name='add_node'),
    path('addnodeexcel/', AddNodeExcelView.as_view(), name='add_node_excel'),
    path('querynode/', views.query_node, name='query_node'),
    path('deletenode/', DeleteNodeView.as_view(), name='delete_node'),
    path('addrelationshipexcel/', AddRelationshipExcelView.as_view(), name='add_relationship'),
    path('queryrelationship/', views.query_relationship, name='query_relationship'),
    path('querynodeexcel/', views.query_node_excel, name='query_node_excel'),
    # path('comparename/', views.compare_name, name='compare_name'),
    path('fuzzymatch/', views.fuzzymatch, name='fuzzymatch'),
    path('getprogress/',  views.getprogress, name='getprogress'),
    path('login/', MyTokenObtainPairView.as_view(), name='login'),
    path('meta/', include(router.urls)),
    path('fmatexcel/', views.fmatexcel, name='fmtexcel'),
    path('qynodedtil/', views.qynodedtil, name='qynodedtil'),
    # path('meta/create_meta_knowledge/', views.MetaKnowledgeViewSet.as_view({'post': 'create_meta_knowledge'}), name='create_meta_knowledge'),
] + router.urls

























