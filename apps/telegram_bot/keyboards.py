from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from .utils import translate_text


def get_main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    builder = ReplyKeyboardBuilder()

    builder.add(KeyboardButton(text=translate_text("🛍 Mahsulotlar", language)))
    builder.add(KeyboardButton(text=translate_text("🛒 Savatcha", language)))
    builder.add(KeyboardButton(text=translate_text("📞 Aloqa", language)))
    builder.add(KeyboardButton(text=translate_text("⚙️ Sozlamalar", language)))

    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)


def get_phone_request_keyboard(language: str) -> ReplyKeyboardMarkup:
    """Get phone request keyboard"""
    builder = ReplyKeyboardBuilder()

    builder.add(KeyboardButton(
        text=translate_text("📱 Telefon raqamni yuborish", language),
        request_contact=True
    ))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_categories_keyboard(categories, language: str, parent_id=None) -> InlineKeyboardMarkup:
    """Get categories inline keyboard"""
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.add(InlineKeyboardButton(
            text=category.name,
            callback_data=f"category_{category.id}"
        ))

    if parent_id:
        builder.add(InlineKeyboardButton(
            text=translate_text("🔙 Orqaga", language),
            callback_data=f"back_to_parent_{parent_id}"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text=translate_text("🏠 Bosh menyu", language),
            callback_data="main_menu"
        ))

    builder.adjust(1)
    return builder.as_markup()


def get_products_keyboard(products, language: str) -> InlineKeyboardMarkup:
    """Get products keyboard"""
    builder = InlineKeyboardBuilder()

    for product in products:
        builder.add(InlineKeyboardButton(
            text=f"{product.name} - {product.min_price} so'm",
            callback_data=f"product_{product.id}"
        ))

    builder.add(InlineKeyboardButton(
        text=translate_text("🔙 Orqaga", language),
        callback_data="back_to_categories"
    ))

    builder.adjust(1)
    return builder.as_markup()


def get_product_colors_keyboard(colors, language: str) -> InlineKeyboardMarkup:
    """Get product colors keyboard"""
    builder = InlineKeyboardBuilder()

    for color in colors:
        builder.add(InlineKeyboardButton(
            text=f"{color.name} - {color.price} so'm",
            callback_data=f"add_to_cart_{color.id}"
        ))

    builder.add(InlineKeyboardButton(
        text=translate_text("🔙 Orqaga", language),
        callback_data="back_to_products"
    ))

    builder.adjust(1)
    return builder.as_markup()


def get_cart_keyboard(language: str) -> InlineKeyboardMarkup:
    """Get cart management keyboard"""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text=translate_text("🗑 Savatchani tozalash", language),
        callback_data="clear_cart"
    ))
    builder.add(InlineKeyboardButton(
        text=translate_text("📝 Buyurtma berish", language),
        callback_data="start_order"
    ))

    builder.adjust(1)
    return builder.as_markup()


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Get language selection keyboard"""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"))
    builder.add(InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"))

    builder.adjust(2)
    return builder.as_markup()
