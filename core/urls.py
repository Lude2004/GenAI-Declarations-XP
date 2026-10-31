from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_declaration, name='create_declaration'),
    path('download-pdf/', views.download_declaration_pdf, name='download_declaration_pdf'),
]