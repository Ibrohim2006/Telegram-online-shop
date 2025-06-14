from django.core.management.base import BaseCommand
from apps.telegram_bot.bot import run_bot


class Command(BaseCommand):
    help = 'Run Aiogram Telegram Bot'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Aiogram Telegram Bot...'))
        run_bot()