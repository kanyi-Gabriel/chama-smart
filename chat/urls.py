from django.urls import path
from . import views

urlpatterns = [
    path('chama/<int:chama_id>/messages/', views.MessageListView.as_view(), name='chat-messages'),
    path('chama/<int:chama_id>/pin/<int:message_id>/', views.PinMessageView.as_view(), name='pin-message'),
]