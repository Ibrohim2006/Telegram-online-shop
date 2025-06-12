from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, TelegramUserSession

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'telegram_id', 'phone_number', 'language', 'is_active_telegram', 'is_staff')
    list_filter = ('is_active_telegram', 'language', 'is_staff')
    search_fields = ('username', 'telegram_id', 'phone_number', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Telegram Info', {'fields': ('telegram_id', 'phone_number', 'language', 'is_active_telegram')}),
    )

@admin.register(TelegramUserSession)
class TelegramUserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_state')
    search_fields = ('user__username', 'user__telegram_id')