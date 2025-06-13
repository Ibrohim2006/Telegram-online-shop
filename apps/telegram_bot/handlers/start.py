from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from django.contrib.auth import get_user_model
from apps.products.models import Cart
from apps.telegram_bot.states import UserRegistration
from apps.telegram_bot.keyboards import get_main_menu_keyboard, get_language_keyboard, get_phone_request_keyboard
from apps.telegram_bot.utils import translate_text, get_or_create_user

User = get_user_model()
router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Handle /start command"""
    telegram_id = message.from_user.id

    try:
        user = User.objects.get(telegram_id=telegram_id)
        if not user.phone_number:
            await message.answer(
                translate_text("Iltimos, telefon raqamingizni yuboring:", user.language),
                reply_markup=get_phone_request_keyboard(user.language)
            )
            await state.set_state(UserRegistration.waiting_for_phone)
        else:
            await show_main_menu(message, user.language)
    except User.DoesNotExist:
        # Show language selection
        await message.answer(
            "Tilni tanlang / Выберите язык:",
            reply_markup=get_language_keyboard()
        )


@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery, state: FSMContext):
    """Handle language selection"""
    await callback.answer()

    language = callback.data.split("_")[1]
    telegram_id = callback.from_user.id

    # Create user with selected language
    user = await get_or_create_user(telegram_id, callback.from_user)
    user.language = language
    user.save()

    # Create cart
    Cart.objects.get_or_create(user=user)

    await callback.message.edit_text(
        translate_text("Ismingizni kiriting:", language)
    )
    await state.set_state(UserRegistration.waiting_for_name)


@router.message(UserRegistration.waiting_for_name)
async def name_received(message: Message, state: FSMContext):
    """Handle name input"""
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    # Update user name
    user.first_name = message.text
    user.save()

    await message.answer(
        translate_text("Iltimos, telefon raqamingizni yuboring:", user.language),
        reply_markup=get_phone_request_keyboard(user.language)
    )
    await state.set_state(UserRegistration.waiting_for_phone)


@router.message(UserRegistration.waiting_for_phone, F.contact)
async def phone_received(message: Message, state: FSMContext):
    """Handle phone contact"""
    telegram_id = message.from_user.id
    contact = message.contact

    if contact.user_id == telegram_id:
        user = User.objects.get(telegram_id=telegram_id)
        user.phone_number = contact.phone_number
        user.save()

        await message.answer(
            translate_text("Rahmat! Endi do'kondan xarid qilishingiz mumkin.", user.language)
        )
        await show_main_menu(message, user.language)
        await state.clear()
    else:
        await message.answer(
            translate_text("Iltimos, o'zingizning telefon raqamingizni yuboring!", user.language)
        )


async def show_main_menu(message: Message, language: str):
    """Show main menu"""
    await message.answer(
        translate_text("🏪 Asosiy menyu", language),
        reply_markup=get_main_menu_keyboard(language)
    )