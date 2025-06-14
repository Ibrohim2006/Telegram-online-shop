from rest_framework import serializers
from apps.products.models import Category, Product, ProductColor, Cart, CartItem
from apps.orders.models import Order, OrderItem
from apps.users.models import User
from decimal import Decimal


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'parent',
            'parent_name',
            'subcategories',
            'category_image',
            'is_active',
            'order',
            'created_at',
            'updated_at',
            'full_path'
        ]
        extra_kwargs = {
            'parent': {'required': False, 'allow_null': True},
            'category_image': {'required': False, 'allow_null': True}
        }

    def get_subcategories(self, obj):
        # Recursively get all subcategories
        subcategories = obj.subcategories.all().order_by('order', 'name')
        serializer = CategorySerializer(subcategories, many=True, context=self.context)
        return serializer.data


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'parent',
            'category_image',
            'is_active',
            'order'
        ]
        extra_kwargs = {
            'parent': {'required': False, 'allow_null': True},
            'category_image': {'required': False, 'allow_null': True}
        }

    def validate_parent(self, value):
        if self.instance and value and self.instance.id == value.id:
            raise serializers.ValidationError("A category cannot be its own parent.")
        return value


class ProductColorSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = ProductColor
        fields = ['id', 'name', 'price', 'is_active', 'images', 'created_at', 'updated_at']

    def get_images(self, obj):
        return [
            {"id": img.id, "image": img.image.url, "order": img.order}
            for img in obj.images.all().order_by('order', 'id')
        ]


class ProductSerializer(serializers.ModelSerializer):
    colors = ProductColorSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'categories', 'product_image',
            'is_active', 'colors', 'min_price', 'created_at', 'updated_at'
        ]

    def get_min_price(self, obj):
        colors = obj.colors.filter(is_active=True)
        return min((color.price for color in colors), default=0)


class CartItemSerializer(serializers.ModelSerializer):
    product_color = ProductColorSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_color', 'quantity', 'total_price', 'created_at', 'updated_at']

    def get_total_price(self, obj) -> Decimal:
        return obj.product_color.price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_amount', 'created_at', 'updated_at']

    def get_total_amount(self, obj):
        return sum(item.total_price for item in obj.items.all())


class OrderItemSerializer(serializers.ModelSerializer):
    product_color = ProductColorSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_color', 'quantity', 'price', 'total_price', 'created_at', 'updated_at']

    def get_total_price(self, obj):
        return obj.total_price


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'total_amount',
            'phone_number', 'address', 'notes',
            'items', 'created_at', 'updated_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'telegram_id', 'phone_number', 'language',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
