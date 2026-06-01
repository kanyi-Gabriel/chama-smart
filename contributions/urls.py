from django.urls import path
from . import views

urlpatterns = [
    path('my/', views.ContributionListView.as_view(), name='my-contributions'),
    path('chama/<int:chama_id>/', views.ChamaContributionsView.as_view(), name='chama-contributions'),
    path('chama/<int:chama_id>/pay/', views.MakeContributionView.as_view(), name='make-contribution'),
    path('penalties/', views.MyPenaltiesView.as_view(), name='my-penalties'),
]