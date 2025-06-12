from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from django.contrib.auth import get_user_model
from apps.products.models import Category, Product, ProductColor, Cart, CartItem
from apps.users.models import TelegramUserSession
from .keyboards import get_main_menu_keyboard, get_categories_keyboard, get_product_keyboard
from .utils import get_user_language, translate_text

User = get_user_model()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    telegram_id = update.effective_user.id

    try:
        user = User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        # Create new user
        user = User.objects.create(
            username=f"user_{telegram_id}",
            telegram_id=telegram_id,
            first_name=update.effective_user.first_name or "",
            last_name=update.effective_user.last_name or ""
        )

        # Create session
        TelegramUserSession.objects.create(user=user)

        # Create cart
        Cart.objects.create(user=user)

        # Ask for phone number
        await update.message.reply_text(
            translate_text("Iltimos, telefon raqamingizni yuboring:", user.language),
            reply_markup=ReplyKeyboardMarkup([
                [{"text": translate_text("📱 Telefon raqamni yuborish", user.language), "request_contact": True}]
            ], resize_keyboard=True)
        )
        return

    # Show main menu
    await show_main_menu(update, context)


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact sharing"""
    telegram_id = update.effective_user.id
    contact = update.message.contact

    if contact.user_id == telegram_id:
        user = User.objects.get(telegram_id=telegram_id)
        user.phone_number = contact.phone_number
        user.save()

        await update.message.reply_text(
            translate_text("Rahmat! Endi do'kondan xarid qilishingiz mumkin.", user.language)
        )
        await show_main_menu(update, context)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    telegram_id = update.effective_user.id
    user = User.objects.get(telegram_id=telegram_id)

    keyboard = get_main_menu_keyboard(user.language)

    await update.message.reply_text(
        translate_text("🏪 Asosiy menyu", user.language),
        reply_markup=keyboard
    )


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show product categories"""
    telegram_id = update.effective_user.id
    user = User.objects.get(telegram_id=telegram_id)

    categories = Category.objects.filter(parent=None, is_active=True)
    keyboard = get_categories_keyboard(categories, user.language)

    await update.message.reply_text(
        translate_text("📂 Kategoriyalarni tanlang:", user.language),
        reply_markup=keyboard
    )


async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection"""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    category_id = int(query.data.split('_')[1])
    category = Category.objects.get(id=category_id)

    # Check if category has subcategories
    subcategories = category.children.filter(is_active=True)

    if subcategories.exists():
        keyboard = get_categories_keyboard(subcategories, user.language, parent_id=category.id)
        await query.edit_message_text(
            translate_text(f"📂 {category.name} - Subkategoriyalar:", user.language),
            reply_markup=keyboard
        )
    else:
        # Show products in this category
        products = category.products.filter(is_active=True)
        if products.exists():
            await show_products_in_category(query, products, user.language)
        else:
            await query.edit_message_text(
                translate_text("Bu kategoriyada hozircha mahsulotlar yo'q.", user.language)
            )


async def show_products_in_category(query, products, language):
    """Show products in selected category"""
    keyboard = []

    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                f"{product.name} - {product.min_price} so'm",
                callback_data=f"product_{product.id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            translate_text("🔙 Orqaga", language),
            callback_data="back_to_categories"
        )
    ])

    await query.edit_message_text(
        translate_text("🛍 Mahsulotlarni tanlang:", language),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_product_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show product details"""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    product_id = int(query.data.split('_')[1])
    product = Product.objects.get(id=product_id)

    # Show product image and details
    colors = product.colors.filter(is_active=True)

    keyboard = get_product_keyboard(product, colors, user.language)

    text = f"🛍 {product.name}\n\n"
    if product.description:
        text += f"{product.description}\n\n"

    text += translate_text("Rangni tanlang:", user.language)

    if product.main_image:
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=product.main_image.url,
            caption=text,
            reply_markup=keyboard
        )
    else:
        await query.edit_message_text(text, reply_markup=keyboard)


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add product to cart"""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    user = User.objects.get(telegram_id=telegram_id)

    color_id = int(query.data.split('_')[2])
    product_color = ProductColor.objects.get(id=color_id)

    cart, created = Cart.objects.get_or_create(user=user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product_color=product_color,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    await query.edit_message_text(
        translate_text(f"✅ {product_color.product.name} ({product_color.name}) savatchaga qo'shildi!", user.language)
    )


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's cart"""
    telegram_id = update.effective_user.id
    user = User.objects.get(telegram_id=telegram_id)

    try:
        cart = Cart.objects.get(user=user)
        items = cart.items.all()

        if not items.exists():
            await update.message.reply_text(
                translate_text("🛒 Savatchangiz bo'sh", user.language)
            )
            return

        text = translate_text("🛒 Savatchangiz:\n\n", user.language)

        for item in items:
            text += f"• {item.product_color.product.name} ({item.product_color.name})\n"
            text += f"  {item.quantity} x {item.product_color.price} = {item.total_price} so'm\n\n"

        text += f"💰 {translate_text('Jami:', user.language)} {cart.total_amount} so'm"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                translate_text("🗑 Savatchani tozalash", user.language),
                callback_data="clear_cart"
            )],
            [InlineKeyboardButton(
                translate_text("📝 Buyurtma berish", user.language),
                callback_data="start_order"
            )]
        ])

        await update.message.reply_text(text, reply_markup=keyboard)

    except Cart.DoesNotExist:
        await update.message.reply_text(
            translate_text("🛒 Savatchangiz bo'sh", user.language)
        )
