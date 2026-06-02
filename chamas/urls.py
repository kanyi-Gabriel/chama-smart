from django.urls import path
from . import views
from . import draw_views

urlpatterns = [
    path('my/', views.MyChamasView.as_view(), name='my-chamas'),
    path('', views.ChamaListCreateView.as_view(), name='chama-list-create'),
    path('<int:pk>/', views.ChamaDetailView.as_view(), name='chama-detail'),
    path('<int:chama_id>/join/', views.JoinChamaView.as_view(), name='join-chama'),
    path('<int:chama_id>/pending/', views.PendingMembersView.as_view(), name='pending-members'),
    path('membership/<int:membership_id>/review/', views.ReviewMembershipView.as_view(), name='review-membership'),
    path('<int:chama_id>/draw/start/', draw_views.StartDrawView.as_view(), name='start-draw'),
    path('<int:chama_id>/draw/history/', draw_views.DrawHistoryView.as_view(), name='draw-history'),
]