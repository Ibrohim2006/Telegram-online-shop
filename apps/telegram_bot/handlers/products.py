from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from django.contrib.auth import get_user_model
from apps.products.models import Cart, CartItem
from apps.telegram_bot.keyboards import get_cart_keyboard
from apps.telegram_bot.utils import translate_text, get_user_language, format_cart_text

User = get_user_model()
router = Router()


@router.message(F.text.in_(["🛒 Savatcha", "🛒 Корзина"]))
async def show_cart(message: Message):
    """Show user's cart"""
    language = get_user_language(message.from_user.id)

    try:
        user = User.objects.get(telegram_id=message.from_user.id)
        cart = Cart.objects.get(user=user)

        text = format_cart_text(cart, language)

        if cart.items.exists():
            await message.answer(
                text,
                reply_markup=get_cart_keyboard(language)
            )
        else:
            await message.answer(text)

    except (User.DoesNotExist, Cart.DoesNotExist):
        await message.answer(
            translate_text("🛒 Savatchangiz bo'sh", language)
        )


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Clear user's cart"""
    await callback.answer()

    language = get_user_language(callback.from_user.id)

    try:
        user = User.objects.get(telegram_id=callback.from_user.id)
        cart = Cart.objects.get(user=user)
        cart.items.all().delete()

        await callback.message.edit_text(
            translate_text("🗑 Savatcha tozalandi!", language)
        )

    except (User.DoesNotExist, Cart.DoesNotExist):
        await callback.message.edit_text(
            translate_text("Xatolik yuz berdi.", language)
        )


@router.callback_query(F.data == "start_order")
async def start_order(callback: CallbackQuery, state: FSMContext):
    """Start order process"""
    await callback.answer()

    language = get_user_language(callback.from_user.id)

    try:
        user = User.objects.get(telegram_id=callback.from_user.id)
        cart = Cart.objects.get(user=user)

        if not cart.items.exists():
            await callback.message.edit_text(
                translate_text("Savatchangiz bo'sh. Avval mahsulot qo'shing.", language)
            )
            return

        await callback.message.edit_text(
            translate_text("📝 Buyurtma jarayoni boshlandi!\n\nManzilni kiriting:", language)
        )

        # Here you can implement order creation states
        # await state.set_state(OrderCreation.entering_address)

    except (User.DoesNotExist, Cart.DoesNotExist):
        await callback.message.edit_text(
            translate_text("Xatolik yuz berdi.", language)
        )
