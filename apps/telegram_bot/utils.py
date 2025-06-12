import os
import django
from django.conf import settings

# Django setup for standalone script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_shop.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import TelegramUserSession

User = get_user_model()


def get_user_language(telegram_id: int) -> str:
    """Get user's preferred language"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        return user.language
    except User.DoesNotExist:
        return 'uz'


def translate_text(text: str, language: str) -> str:
    """Simple translation function"""
    translations = {
        'uz': {
            "Iltimos, telefon raqamingizni yuboring:": "Iltimos, telefon raqamingizni yuboring:",
            "📱 Telefon raqamni yuborish": "📱 Telefon raqamni yuborish",
            "Rahmat! Endi do'kondan xarid qilishingiz mumkin.": "Rahmat! Endi do'kondan xarid qilishingiz mumkin.",
            "🏪 Asosiy menyu": "🏪 Asosiy menyu",
            "🛍 Mahsulotlar": "🛍 Mahsulotlar",
            "🛒 Savatcha": "🛒 Savatcha",
            "📞 Aloqa": "📞 Aloqa",
            "⚙️ Sozlamalar": "⚙️ Sozlamalar",
            "📂 Kategoriyalarni tanlang:": "📂 Kategoriyalarni tanlang:",
            "🔙 Orqaga": "🔙 Orqaga",
            "🏠 Bosh menyu": "🏠 Bosh menyu",
            "Rangni tanlang:": "Rangni tanlang:",
            "🛒 Savatchangiz bo'sh": "🛒 Savatchangiz bo'sh",
            "🛒 Savatchangiz:\n\n": "🛒 Savatchangiz:\n\n",
            "Jami:": "Jami:",
            "🗑 Savatchani tozalash": "🗑 Savatchani tozalash",
            "📝 Buyurtma berish": "📝 Buyurtma berish",
            "Ismingizni kiriting:": "Ismingizni kiriting:",
            "Tilni tanlang:": "Tilni tanlang:",
        },
        'ru': {
            "Iltimos, telefon raqamingizni yuboring:": "Пожалуйста, отправьте свой номер телефона:",
            "📱 Telefon raqamni yuborish": "📱 Отправить номер телефона",
            "Rahmat! Endi do'kondan xarid qilishingiz mumkin.": "Спасибо! Теперь вы можете делать покупки.",
            "🏪 Asosiy menyu": "🏪 Главное меню",
            "🛍 Mahsulotlar": "🛍 Товары",
            "🛒 Savatcha": "🛒 Корзина",
            "📞 Aloqa": "📞 Контакты",
            "⚙️ Sozlamalar": "⚙️ Настройки",
            "📂 Kategoriyalarni tanlang:": "📂 Выберите категорию:",
            "🔙 Orqaga": "🔙 Назад",
            "🏠 Bosh menyu": "🏠 Главное меню",
            "Rangni tanlang:": "Выберите цвет:",
            "🛒 Savatchangiz bo'sh": "🛒 Ваша корзина пуста",
            "🛒 Savatchangiz:\n\n": "🛒 Ваша корзина:\n\n",
            "Jami:": "Итого:",
            "🗑 Savatchani tozalash": "🗑 Очистить корзину",
            "📝 Buyurtma berish": "📝 Оформить заказ",
            "Ismingizni kiriting:": "Введите ваше имя:",
            "Tilni tanlang:": "Выберите язык:",
        }
    }

    return translations.get(language, {}).get(text, text)


async def get_or_create_user(telegram_id: int, telegram_user) -> User:
    """Get or create user from telegram data"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        return user
    except User.DoesNotExist:
        user = User.objects.create(
            username=f"user_{telegram_id}",
            telegram_id=telegram_id,
            first_name=telegram_user.first_name or "",
            last_name=telegram_user.last_name or ""
        )

        # Create session
        TelegramUserSession.objects.create(user=user)

        return user


def format_cart_text(cart, language: str) -> str:
    """Format cart items text"""
    if not cart.items.exists():
        return translate_text("🛒 Savatchangiz bo'sh", language)

    text = translate_text("🛒 Savatchangiz:\n\n", language)

    for item in cart.items.all():
        text += f"• {item.product_color.product.name} ({item.product_color.name})\n"
        text += f"  {item.quantity} x {item.product_color.price} = {item.total_price} so'm\n\n"

    text += f"💰 {translate_text('Jami:', language)} {cart.total_amount} so'm"

    return text
