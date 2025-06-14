from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from django.contrib.auth import get_user_model
from apps.telegram_bot.keyboards import (
    get_categories_keyboard,
    get_products_keyboard,
    get_product_keyboard
)
from apps.telegram_bot.utils import translate_text, get_user_language, get_user_by_telegram_id
from apps.products.models import Category, Product, ProductColor, CartItem, Cart

User = get_user_model()
router = Router()


@router.message(F.text.in_(["🛍 Mahsulotlar", "🛍 Товары"]))
async def show_categories(message: Message):
    try:
        language = await get_user_language(message.from_user.id)
        categories = [category async for category in Category.objects.filter(parent=None, is_active=True)]
        if not categories:
            await message.answer(translate_text("Kategoriyalar topilmadi", language))
            return

        keyboard = get_categories_keyboard(categories, language)

        await message.answer(
            translate_text("📂 Kategoriyalarni tanlang:", language),
            reply_markup=keyboard
        )

    except Exception as e:
        await message.answer(
            translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.",
                           language or 'uz')
        )


@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery):
    try:
        await callback.answer()
        language = await get_user_language(callback.from_user.id)
        category_id = int(callback.data.split('_')[1])

        category = await Category.objects.aget(id=category_id)

        subcategories = [
            subcat async for subcat in
            Category.objects.filter(parent=category, is_active=True)
        ]

        if subcategories:
            await callback.message.edit_text(
                translate_text(f"📂 {category.name} - Kategoriyalar:", language),
                reply_markup=get_categories_keyboard(subcategories, language, parent_id=category.id)
            )
            return

        products = [
            product async for product in
            category.products.filter(is_active=True)
        ]

        if not products:
            await callback.message.edit_text(
                translate_text("Bu kategoriyada hozircha mahsulotlar yo'q", language)
            )
            return

        await callback.message.edit_text(
            translate_text("🛍 Mahsulotlarni tanlang:", language),
            reply_markup=get_products_keyboard(products, language)
        )

    except Exception as e:
        print(f"Xato yuz berdi: {e}")
        await callback.message.edit_text(
            translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.", language)
        )


@router.callback_query(F.data.startswith("product_"))
async def show_product_details(callback: CallbackQuery):
    """Mahsulot tafsilotlarini ko'rsatish"""
    try:
        await callback.answer()
        language = await get_user_language(callback.from_user.id)
        product_id = int(callback.data.split('_')[1])

        product = await Product.objects.select_related('category').aget(id=product_id)
        colors = [color async for color in product.colors.filter(is_active=True)]

        if not colors:
            await callback.message.edit_text(
                translate_text("Bu mahsulotda hozircha ranglar mavjud emas", language)
            )
            return

        text = f"🛍 {product.name}\n\n"
        if product.description:
            text += f"{product.description}\n\n"
        text += translate_text("Rangni tanlang:", language)

        await callback.message.edit_text(
            text,
            reply_markup=get_product_keyboard(product, colors, language)
        )

    except Product.DoesNotExist:
        await callback.message.edit_text(
            translate_text("Mahsulot topilmadi", language)
        )
    except Exception as e:
        print(f"Xato tafsilotlari: {e}")
        await callback.message.edit_text(
            translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.", language)
        )


@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery):
    """Add selected product to cart"""
    try:
        await callback.answer()
        language = await get_user_language(callback.from_user.id)
        user = await get_user_by_telegram_id(callback.from_user.id)
        color_id = int(callback.data.split('_')[3])

        color = await ProductColor.objects.select_related('product').aget(id=color_id)
        cart, _ = await Cart.objects.aget_or_create(user=user)

        item, created = await CartItem.objects.aget_or_create(
            cart=cart,
            product_color=color,
            defaults={'quantity': 1}
        )

        if not created:
            item.quantity += 1
            await item.asave()

        await callback.answer(
            translate_text(f"{color.product.name} ({color.name}) savatchaga qo'shildi!", language),
            show_alert=True
        )

    except Exception as e:
        await callback.answer(
            translate_text("Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.", language),
            show_alert=True
        )
