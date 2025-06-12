from rest_framework import serializers
from apps.products.models import Category, Product, ProductColor, Cart, CartItem
from apps.orders.models import Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'image', 'is_active', 'order', 'children']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []


class ProductColorSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = ProductColor
        fields = ['id', 'name', 'price', 'is_active', 'images']

    def get_images(self, obj):
        return [img.image.url for img in obj.images.all()]


class ProductSerializer(serializers.ModelSerializer):
    colors = ProductColorSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    min_price = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'categories', 'main_image',
                  'is_active', 'colors', 'min_price', 'created_at']


class CartItemSerializer(serializers.ModelSerializer):
    product_color = ProductColorSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_color', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_amount', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_color = ProductColorSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_color', 'quantity', 'price', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total_amount', 'phone_number',
                  'address', 'notes', 'items', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'telegram_id',
                  'phone_number', 'language', 'is_active_telegram', 'created_at']
