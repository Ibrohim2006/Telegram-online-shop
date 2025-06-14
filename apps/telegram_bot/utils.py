import os
import django
from django.conf import settings
from asgiref.sync import sync_to_async

# Django setup for standalone script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_shop.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import TelegramUserSession
from apps.products.models import Cart, CartItem

User = get_user_model()


# Database operations
@sync_to_async
def get_user_language(telegram_id: int) -> str:
    """Get user's preferred language (async)"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        return user.language
    except User.DoesNotExist:
        return 'uz'


@sync_to_async
def get_user_by_telegram_id(telegram_id: int):
    """Get user by telegram ID (async)"""
    try:
        return User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return None


@sync_to_async
def get_or_create_user(telegram_id: int, telegram_user) -> User:
    """Get or create user from telegram data (async)"""
    try:
        return User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        user = User.objects.create(
            username=f"user_{telegram_id}",
            telegram_id=telegram_id,
            first_name=telegram_user.first_name or "",
            last_name=telegram_user.last_name or ""
        )
        TelegramUserSession.objects.create(user=user)
        return user


@sync_to_async
def get_user_cart(user):
    """Get user's cart (async)"""
    try:
        return Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        return None


@sync_to_async
def create_cart(user):
    """Create cart for user (async)"""
    return Cart.objects.create(user=user)


@sync_to_async
def cart_has_items(cart):
    """Check if cart has items (async)"""
    return cart.items.exists()


@sync_to_async
def get_cart_items(cart):
    """Get cart items (async)"""
    return list(cart.items.all())


@sync_to_async
def clear_cart_items(cart):
    """Clear all items from cart (async)"""
    cart.items.all().delete()


@sync_to_async
def format_cart_text(cart, language: str) -> str:
    """Format cart items text (async)"""
    if not cart.items.exists():
        return translate_text("🛒 Savatchangiz bo'sh", language)

    text = translate_text("🛒 Savatchangiz:\n\n", language)
    items = cart.items.all()

    for item in items:
        text += f"• {item.product_color.product.name} ({item.product_color.name})\n"
        text += f"  {item.quantity} x {item.product_color.price} = {item.total_price} so'm\n\n"

    text += f"💰 {translate_text('Jami:', language)} {cart.total_amount} so'm"
    return text


# Non-database functions
def translate_text(text: str, language: str) -> str:
    """Simple translation function with fallback (sync)"""
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

    lang_translations = translations.get(language, translations['uz'])
    return lang_translations.get(text, text)


# Additional utility functions
@sync_to_async
def update_user_language(user, language: str):
    """Update user's language preference (async)"""
    user.language = language
    user.save()


@sync_to_async
def update_user_phone(user, phone_number: str):
    """Update user's phone number (async)"""
    user.phone_number = phone_number
    user.save()


@sync_to_async
def add_to_cart(user, product_color, quantity=1):
    """Add item to cart (async)"""
    cart, _ = Cart.objects.get_or_create(user=user)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product_color=product_color,
        defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()
    return item