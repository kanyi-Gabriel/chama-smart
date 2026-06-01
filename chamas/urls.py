from django.urls import path
from . import views

urlpatterns = [
    path('', views.ChamaListCreateView.as_view(), name='chama-list-create'),
    path('<int:pk>/', views.ChamaDetailView.as_view(), name='chama-detail'),
    path('<int:chama_id>/join/', views.JoinChamaView.as_view(), name='join-chama'),
    path('my/', views.MyChamasView.as_view(), name='my-chamas'),
]