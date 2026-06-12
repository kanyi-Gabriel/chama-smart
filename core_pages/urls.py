from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('chamas/', views.chamas_view, name='chamas'),
    path('chamas/<int:chama_id>/', views.chama_detail_view, name='chama_detail'),
    path('contributions/', views.contributions_view, name='contributions'),
    path('loans/', views.loans_view, name='loans'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('draw/', views.draw, name='draw'),
    path('chamas/<int:chama_id>/chat/', views.chat_view, name='chat'),
]