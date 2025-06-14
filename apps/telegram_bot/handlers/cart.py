from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from django.contrib.auth import get_user_model
from apps.telegram_bot.keyboards import get_cart_keyboard, get_order_confirmation_keyboard
from apps.telegram_bot.utils import (
    translate_text,
    get_user_language,
    get_user_by_telegram_id,
    get_user_cart,
    cart_has_items,
    clear_cart_items,
    format_cart_text
)
from apps.telegram_bot.states import OrderCreation
from apps.products.models import CartItem

User = get_user_model()
router = Router()


@router.message(F.text.in_(["🛒 Savatcha", "🛒 Корзина"]))
async def show_cart(message: Message):
    """Show user's cart with all items"""
    try:
        language = await get_user_language(message.from_user.id)
        user = await get_user_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer(translate_text("🛒 Savatchangiz bo'sh", language))
            return

        cart = await get_user_cart(user)
        if not cart:
            await message.answer(translate_text("🛒 Savatchangiz bo'sh", language))
            return

        text = await format_cart_text(cart, language)
        has_items = await cart_has_items(cart)

        if has_items:
            await message.answer(text, reply_markup=get_cart_keyboard(language))
        else:
            await message.answer(text)

    except Exception as e:
        await message.answer(translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.",
                                          await get_user_language(message.from_user.id)))


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Clear all items from user's cart"""
    try:
        await callback.answer()
        language = await get_user_language(callback.from_user.id)
        user = await get_user_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.message.edit_text(translate_text("Xatolik yuz berdi.", language))
            return

        cart = await get_user_cart(user)
        if not cart:
            await callback.message.edit_text(translate_text("Xatolik yuz berdi.", language))
            return

        await clear_cart_items(cart)
        await callback.message.edit_text(translate_text("🗑 Savatcha tozalandi!", language))

    except Exception as e:
        await callback.message.edit_text(translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.",
                                                      await get_user_language(callback.from_user.id)))


@router.callback_query(F.data.startswith("remove_item_"))
async def remove_item_from_cart(callback: CallbackQuery):
    """Remove specific item from cart"""
    try:
        await callback.answer()
        language = await get_user_language(callback.from_user.id)
        user = await get_user_by_telegram_id(callback.from_user.id)
        item_id = int(callback.data.split('_')[2])

        if not user:
            await callback.message.edit_text(translate_text("Xatolik yuz berdi.", language))
            return

        item = await CartItem.objects.aget(id=item_id)
        await item.adelete()

        await callback.answer(translate_text("Mahsulot savatchadan o'chirildi!", language), show_alert=True)
        await show_cart(callback.message)

    except Exception as e:
        await callback.message.edit_text(translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.",
                                                      await get_user_language(callback.from_user.id)))


@router.callback_query(F.data == "start_order")
async def start_order(callback: CallbackQuery, state: FSMContext):
    """Start order process"""
    try:
        await callback.answer()
        language = await get_user_language(callback.from_user.id)
        user = await get_user_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.message.edit_text(translate_text("Xatolik yuz berdi.", language))
            return

        cart = await get_user_cart(user)
        has_items = await cart_has_items(cart) if cart else False

        if not cart or not has_items:
            await callback.message.edit_text(
                translate_text("Savatchangiz bo'sh. Avval mahsulot qo'shing.", language)
            )
            return

        await callback.message.edit_text(
            translate_text("📝 Buyurtma jarayoni boshlandi!\n\nManzilni kiriting:", language)
        )
        await state.set_state(OrderCreation.entering_address)

    except Exception as e:
        await callback.message.edit_text(translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.",
                                                      await get_user_language(callback.from_user.id)))


@router.message(OrderCreation.entering_address)
async def process_address(message: Message, state: FSMContext):
    """Process delivery address for order"""
    try:
        language = await get_user_language(message.from_user.id)
        user = await get_user_by_telegram_id(message.from_user.id)
        cart = await get_user_cart(user)

        await state.update_data(address=message.text)
        text = await format_cart_text(cart, language)
        text += f"\n\n📍 {translate_text('Manzil:', language)} {message.text}"
        text += f"\n\n{translate_text('Buyurtmani tasdiqlaysizmi?', language)}"

        await message.answer(
            text,
            reply_markup=get_order_confirmation_keyboard(language)
        )
        await state.set_state(OrderCreation.confirming_order)

    except Exception as e:
        await message.answer(translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.", language))


@router.callback_query(F.data == "confirm_order", OrderCreation.confirming_order)
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Confirm and finalize the order"""
    try:
        await callback.answer()
        language = await get_user_language(callback.from_user.id)
        user = await get_user_by_telegram_id(callback.from_user.id)
        cart = await get_user_cart(user)
        data = await state.get_data()

        # Here you would typically create an order in database
        # For now, we'll just show a confirmation
        await clear_cart_items(cart)
        await callback.message.edit_text(
            translate_text("✅ Buyurtmangiz qabul qilindi! Tez orada operator siz bilan bog'lanadi.", language)
        )
        await state.clear()

    except Exception as e:
        await callback.message.edit_text(translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.", language))