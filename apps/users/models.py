from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    LANGUAGE_UZBEK = 'uz'
    LANGUAGE_RUSSIAN = 'ru'

    LANGUAGE_CHOICES = [
        (LANGUAGE_UZBEK, 'Uzbek'),
        (LANGUAGE_RUSSIAN, 'Russian'),
    ]

    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_UZBEK)
    is_active_telegram = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.telegram_id or 'No Telegram ID'})"


class TelegramUserSession(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='telegram_session')
    current_state = models.CharField(max_length=50, default='main_menu')
    current_category = models.PositiveIntegerField(null=True, blank=True)
    current_product = models.PositiveIntegerField(null=True, blank=True)
    session_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Session for {self.user.username}"
