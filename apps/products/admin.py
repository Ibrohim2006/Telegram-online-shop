from django.contrib import admin
from .models import Category, Product, ProductColor, ProductColorImage, Cart, CartItem

class ProductColorImageInline(admin.TabularInline):
    model = ProductColorImage
    extra = 1

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'product__name')
    inlines = [ProductColorImageInline]

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_price', 'is_active', 'created_at')
    list_filter = ('is_active', 'categories')
    search_fields = ('name',)
    filter_horizontal = ('categories',)
    inlines = [ProductColorInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'order')
    list_filter = ('is_active', 'parent')
    search_fields = ('name',)

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_amount', 'created_at')
    search_fields = ('user__username', 'user__telegram_id')
    inlines = [CartItemInline]