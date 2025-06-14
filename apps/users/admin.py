from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TelegramUserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'telegram_id', 'phone_number',
        'language', 'is_active'
    )
    list_filter = ('is_active', 'language')
    search_fields = ('username', 'telegram_id', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Telegram Info', {
            'fields': (
                'telegram_id', 'phone_number', 'language',
                'created_at', 'updated_at'
            ),
        }),
    )


@admin.register(TelegramUserSession)
class TelegramUserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_state', 'current_category', 'current_product')
    search_fields = ('user__username', 'user__telegram_id')
    readonly_fields = ('session_data',)
    list_filter = ('current_state',)
    ordering = ('user__username',)
