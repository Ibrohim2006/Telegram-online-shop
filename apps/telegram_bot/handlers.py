from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.contrib.auth import get_user_model
from apps.products.models import Category, Product, Cart, CartItem, ProductColor
from apps.users.models import TelegramUserSession
from .keyboards import get_main_menu_keyboard, get_categories_keyboard, get_product_keyboard, get_cart_keyboard
from .utils import translate_text
from .states import OrderCreation

User = get_user_model()

router = Router()


# Start command remains the same
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


# Contact handler remains the same
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


async def show_main_menu(message: types.Message, user: User):
    keyboard = get_main_menu_keyboard(user.language)
    await message.answer(
        translate_text("🏪 Asosiy menyu", user.language),
        reply_markup=keyboard
    )


# Categories and products browsing
@router.message(F.text.in_(["🛍 Mahsulotlar", "🛍 Товары"]))
async def show_categories(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    categories = Category.objects.filter(parent=None, is_active=True)
    keyboard = get_categories_keyboard(categories, user.language)

    await message.answer(
        translate_text("📂 Kategoriyalarni tanlang:", user.language),
        reply_markup=keyboard
    )


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

    builder.adjust(1)

    await callback_query.message.edit_text(
        translate_text("🛍 Mahsulotlarni tanlang:", language),
        reply_markup=builder.as_markup()
    )


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


# Add to cart functionality
@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart_handler(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = callback_query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    color_id = int(callback_query.data.split('_')[3])

    try:
        color = ProductColor.objects.get(id=color_id)
        cart, created = Cart.objects.get_or_create(user=user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_color=color,
            defaults={'quantity': 1}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        await callback_query.answer(
            translate_text(f"{color.product.name} ({color.name}) savatchaga qo'shildi!", user.language),
            show_alert=True
        )
    except Exception as e:
        await callback_query.answer(
            translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.", user.language),
            show_alert=True
        )


# Cart management
@router.message(F.text.in_(["🛒 Savatcha", "🛒 Корзина"]))
async def show_cart(message: types.Message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    try:
        cart = Cart.objects.get(user=user)
        items = cart.items.all()

        if not items.exists():
            await message.answer(translate_text("🛒 Savatchangiz bo'sh", user.language))
            return

        text = translate_text("🛒 Savatchangiz:\n\n", user.language)
        total = 0

        for item in items:
            product = item.product_color.product
            color = item.product_color
            item_total = item.quantity * color.price
            total += item_total

            text += f"• {product.name} ({color.name})\n"
            text += f"  {item.quantity} x {color.price} = {item_total} so'm\n"
            text += f"  [<a href='remove_item_{item.id}'>❌ O'chirish</a>]\n\n"

        text += f"\n💰 {translate_text('Jami:', user.language)} {total} so'm"

        keyboard = get_cart_keyboard(user.language)
        await message.answer(text, reply_markup=keyboard)

    except Cart.DoesNotExist:
        await message.answer(translate_text("🛒 Savatchangiz bo'sh", user.language))


# Remove item from cart
@router.callback_query(F.data.startswith("remove_item_"))
async def remove_item_from_cart(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    item_id = int(callback_query.data.split('_')[2])

    try:
        item = CartItem.objects.get(id=item_id)
        item.delete()

        await callback_query.answer(
            translate_text("Mahsulot savatchadan o'chirildi!", user.language),
            show_alert=True
        )

        # Refresh the cart view
        await show_cart(callback_query.message)

    except CartItem.DoesNotExist:
        await callback_query.answer(
            translate_text("Mahsulot topilmadi!", user.language),
            show_alert=True
        )


# Clear cart
@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    try:
        cart = Cart.objects.get(user=user)
        cart.items.all().delete()

        await callback_query.answer(
            translate_text("Savatcha tozalandi!", user.language),
            show_alert=True
        )

        await callback_query.message.edit_text(
            translate_text("🛒 Savatchangiz bo'sh", user.language)
        )
    except Cart.DoesNotExist:
        await callback_query.answer(
            translate_text("Savatcha topilmadi!", user.language),
            show_alert=True
        )


# Start order process
@router.callback_query(F.data == "start_order")
async def start_order_handler(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = callback_query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    try:
        cart = Cart.objects.get(user=user)
        if not cart.items.exists():
            await callback_query.answer(
                translate_text("Savatchangiz bo'sh. Avval mahsulot qo'shing.", user.language),
                show_alert=True
            )
            return

        await state.set_state(OrderCreation.entering_address)
        await callback_query.message.answer(
            translate_text("📝 Buyurtma berish:\n\nIltimos, yetkazib berish manzilini yuboring:", user.language)
        )

    except Cart.DoesNotExist:
        await callback_query.answer(
            translate_text("Savatcha topilmadi!", user.language),
            show_alert=True
        )


# Address handler for order
@router.message(OrderCreation.entering_address)
async def process_address(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    await state.update_data(address=message.text)
    await state.set_state(OrderCreation.confirming_order)

    cart = Cart.objects.get(user=user)
    items = cart.items.all()
    total = sum(item.quantity * item.product_color.price for item in items)

    text = translate_text("📝 Buyurtma tafsilotlari:\n\n", user.language)
    text += translate_text("📦 Mahsulotlar:\n", user.language)

    for item in items:
        product = item.product_color.product
        color = item.product_color
        item_total = item.quantity * color.price

        text += f"• {product.name} ({color.name}) - {item.quantity} x {color.price} = {item_total} so'm\n"

    text += f"\n💰 {translate_text('Jami:', user.language)} {total} so'm\n"
    text += f"\n🏠 {translate_text('Manzil:', user.language)} {message.text}\n\n"
    text += translate_text("Buyurtmani tasdiqlaysizmi?", user.language)

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text=translate_text("✅ Tasdiqlash", user.language),
        callback_data="confirm_order"
    ))
    keyboard.add(InlineKeyboardButton(
        text=translate_text("❌ Bekor qilish", user.language),
        callback_data="cancel_order"
    ))

    await message.answer(text, reply_markup=keyboard.as_markup())


# Confirm order
@router.callback_query(F.data == "confirm_order")
async def confirm_order_handler(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = callback_query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    try:
        data = await state.get_data()
        address = data.get('address')

        # Here you would typically create an order in your database
        # For now, we'll just show a confirmation message

        await callback_query.message.edit_text(
            translate_text("✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.", user.language)
        )

        # Clear the cart
        cart = Cart.objects.get(user=user)
        cart.items.all().delete()

        await state.clear()

    except Exception as e:
        await callback_query.message.edit_text(
            translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.", user.language)
        )


# Cancel order
@router.callback_query(F.data == "cancel_order")
async def cancel_order_handler(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = callback_query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    await callback_query.message.edit_text(
        translate_text("❌ Buyurtma bekor qilindi.", user.language)
    )
    await state.clear()
    await show_main_menu(callback_query.message, user)
