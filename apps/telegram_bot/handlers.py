from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.contrib.auth import get_user_model
from apps.products.models import Category, Product, Cart
from apps.users.models import TelegramUserSession
from .keyboards import get_main_menu_keyboard, get_categories_keyboard, get_product_keyboard
from .utils import translate_text

User = get_user_model()

router = Router()


# Start komandasi
@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    try:
        user = User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        user = User.objects.create(
            username=f"user_{telegram_id}",
            telegram_id=telegram_id,
            first_name=message.from_user.first_name or "",
            last_name=message.from_user.last_name or ""
        )
        TelegramUserSession.objects.create(user=user)
        Cart.objects.create(user=user)

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(
                    text=translate_text("📱 Telefon raqamni yuborish", user.language),
                    request_contact=True
                )]
            ],
            resize_keyboard=True
        )
        await message.answer(
            translate_text("Iltimos, telefon raqamingizni yuboring:", user.language),
            reply_markup=keyboard
        )
        return

    await show_main_menu(message, user)


# Telefon raqam qabul qilish
@router.message(F.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    contact = message.contact

    if contact.user_id == telegram_id:
        user = User.objects.get(telegram_id=telegram_id)
        user.phone_number = contact.phone_number
        user.save()

        await message.answer(
            translate_text("Rahmat! Endi do'kondan xarid qilishingiz mumkin.", user.language)
        )
        await show_main_menu(message, user)


# Asosiy menu
async def show_main_menu(message: types.Message, user: User):
    keyboard = get_main_menu_keyboard(user.language)
    await message.answer(
        translate_text("🏪 Asosiy menyu", user.language),
        reply_markup=keyboard
    )


# Kategoriya ko'rsatish
@router.message(F.text == "📂 Kategoriyalar")  # Bu joyda sen main menu tugmasi textiga mos yoz
async def show_categories(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    categories = Category.objects.filter(parent=None, is_active=True)
    keyboard = get_categories_keyboard(categories, user.language)

    await message.answer(
        translate_text("📂 Kategoriyalarni tanlang:", user.language),
        reply_markup=keyboard
    )


# Callback - category tanlash
@router.callback_query(F.data.startswith("category_"))
async def handle_category_selection(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = callback_query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    category_id = int(callback_query.data.split('_')[1])
    category = Category.objects.get(id=category_id)
    subcategories = category.children.filter(is_active=True)

    if subcategories.exists():
        keyboard = get_categories_keyboard(subcategories, user.language, parent_id=category.id)
        await callback_query.message.edit_text(
            translate_text(f"📂 {category.name} - Subkategoriyalar:", user.language),
            reply_markup=keyboard
        )
    else:
        products = category.products.filter(is_active=True)
        if products.exists():
            await show_products_in_category(callback_query, products, user.language)
        else:
            await callback_query.message.edit_text(
                translate_text("Bu kategoriyada hozircha mahsulotlar yo'q.", user.language)
            )


# Mahsulotlarni ko'rsatish
async def show_products_in_category(callback_query, products, language):
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

    builder.adjust(1)  # Har bir qatorga 1 tadan tugma

    await callback_query.message.edit_text(
        translate_text("🛍 Mahsulotlarni tanlang:", language),
        reply_markup=builder.as_markup()
    )


# Mahsulot detallarini ko'rsatish
@router.callback_query(F.data.startswith("product_"))
async def show_product_details(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = callback_query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    product_id = int(callback_query.data.split('_')[1])
    product = Product.objects.get(id=product_id)
    colors = product.colors.filter(is_active=True)
    keyboard = get_product_keyboard(product, colors, user.language)

    text = f"🛍 {product.name}\n\n"
    if product.description:
        text += f"{product.description}\n\n"
    text += translate_text("Rangni tanlang:", user.language)

    if product.main_image:
        await callback_query.message.answer_photo(
            photo=product.main_image.url,
            caption=text,
            reply_markup=keyboard
        )
    else:
        await callback_query.message.edit_text(text, reply_markup=keyboard)
