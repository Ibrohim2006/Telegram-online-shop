from django.contrib import admin
from .models import Category, Product, ProductColor, ProductColorImage, Cart, CartItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name',)
    ordering = ('order', 'name')


class ProductColorImageInline(admin.TabularInline):
    model = ProductColorImage
    extra = 1
    ordering = ('order',)


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'price', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'product__name')
    ordering = ('product__name', 'name')
    inlines = [ProductColorImageInline]


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    ordering = ('name',)
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_price', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'categories')
    search_fields = ('name',)
    filter_horizontal = ('categories',)
    ordering = ('-created_at',)
    inlines = [ProductColorInline]


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('total_price',)
    ordering = ('-created_at',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_amount', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__telegram_id')
    inlines = [CartItemInline]
    ordering = ('-created_at',)
