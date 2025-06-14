from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from apps.products.models import Cart
from apps.telegram_bot.states import UserRegistration
from apps.telegram_bot.keyboards import get_main_menu_keyboard, get_language_keyboard, get_phone_request_keyboard
from apps.telegram_bot.utils import translate_text

User = get_user_model()
router = Router()


# Async database operations
@sync_to_async
def get_user_by_telegram_id(telegram_id):
    try:
        return User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return None


@sync_to_async
def create_user(telegram_id, first_name, last_name, language='uz'):
    user = User.objects.create(
        username=f"user_{telegram_id}",
        telegram_id=telegram_id,
        first_name=first_name or "",
        last_name=last_name or "",
        language=language
    )
    Cart.objects.create(user=user)
    return user


@sync_to_async
def update_user_phone(user, phone_number):
    user.phone_number = phone_number
    user.save()
    return user


@sync_to_async
def update_user_name(user, name):
    user.first_name = name
    user.save()
    return user


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id(telegram_id)

    if user:
        if not user.phone_number:
            await message.answer(
                translate_text("Iltimos, telefon raqamingizni yuboring:", user.language),
                reply_markup=get_phone_request_keyboard(user.language)
            )
            await state.set_state(UserRegistration.waiting_for_phone)
        else:
            await show_main_menu(message, user.language)
    else:
        await message.answer(
            "Tilni tanlang / Выберите язык:",
            reply_markup=get_language_keyboard()
        )


@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    language = callback.data.split("_")[1]
    telegram_user = callback.from_user

    user = await create_user(
        telegram_id=telegram_user.id,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
        language=language
    )

    await callback.message.edit_text(
        translate_text("Ismingizni kiriting:", language)
    )
    await state.set_state(UserRegistration.waiting_for_name)


@router.message(UserRegistration.waiting_for_name)
async def name_received(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id(telegram_id)

    if user:
        await update_user_name(user, message.text)
        await message.answer(
            translate_text("Iltimos, telefon raqamingizni yuboring:", user.language),
            reply_markup=get_phone_request_keyboard(user.language)
        )
        await state.set_state(UserRegistration.waiting_for_phone)


@router.message(UserRegistration.waiting_for_phone, F.contact)
async def phone_received(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    contact = message.contact
    user = await get_user_by_telegram_id(telegram_id)

    if user and contact.user_id == telegram_id:
        await update_user_phone(user, contact.phone_number)
        await message.answer(
            translate_text("Rahmat! Endi do'kondan xarid qilishingiz mumkin.", user.language)
        )
        await show_main_menu(message, user.language)
        await state.clear()
    else:
        language = user.language if user else 'uz'
        await message.answer(
            translate_text("Iltimos, o'zingizning telefon raqamingizni yuboring!", language)
        )


async def show_main_menu(message: Message, language: str):
    await message.answer(
        translate_text("🏪 Asosiy menyu", language),
        reply_markup=get_main_menu_keyboard(language)
    )