from django.db import models
from django.contrib.auth.models import AbstractUser

from apps.users.utils import validate_phone_number

LANGUAGE_CHOICES = [
    ('uz', 'Uzbek'),
    ('ru', 'Russian'),
]


class User(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name="Telegram ID")
    phone_number = models.CharField(max_length=13, blank=True, validators=[validate_phone_number],
                                    verbose_name="Phone number")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='uz', verbose_name="Language")
    is_active = models.BooleanField(default=True, verbose_name="Is active")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    def __str__(self):
        telegram_display = self.telegram_id if self.telegram_id else 'No Telegram ID'
        return f"{self.username} ({telegram_display})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "user"
        ordering = ['-created_at']


class TelegramUserSession(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='telegram_session', verbose_name="User")
    current_state = models.CharField(max_length=50, default='main_menu', verbose_name="Current state")
    current_category = models.PositiveIntegerField(null=True, blank=True, verbose_name="Current category")
    current_product = models.PositiveIntegerField(null=True, blank=True, verbose_name="Current product")
    session_data = models.JSONField(default=dict, blank=True, verbose_name="Session data")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    def __str__(self):
        return f"Session for {self.user.username}"

    class Meta:
        verbose_name = "Telegram User Session"
        verbose_name_plural = "Telegram User Sessions"
        db_table = "telegram_user_session"
        ordering = ['-updated_at']
