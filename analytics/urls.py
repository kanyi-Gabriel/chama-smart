from django.urls import path
from . import views

urlpatterns = [
    path('score/', views.MyCreditScoreView.as_view(), name='my-score'),
    path('score/<int:chama_id>/', views.MyCreditScoreView.as_view(), name='my-chama-score'),
    path('chama/<int:chama_id>/', views.ChamaAnalyticsView.as_view(), name='chama-analytics'),
]