from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'chama', 'message_type', 'is_pinned', 'timestamp']
    list_filter = ['message_type', 'is_pinned', 'chama']
    search_fields = ['sender__phone_number', 'content']