from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from apps.products.models import Category, Product, ProductColor, Cart, CartItem
from apps.orders.models import Order
from .serializers import (
    CategorySerializer, ProductSerializer, CartSerializer,
    OrderSerializer, UserSerializer
)

User = get_user_model()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree"""
        root_categories = Category.objects.filter(parent=None, is_active=True)
        serializer = self.get_serializer(root_categories, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get products by category"""
        category_id = request.query_params.get('category_id')
        if category_id:
            products = Product.objects.filter(
                categories__id=category_id,
                is_active=True
            ).distinct()
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        return Response({'error': 'category_id required'}, status=400)


class CartViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Cart.objects.all().select_related('user').prefetch_related('items__product_color')

    @action(detail=False, methods=['get'])
    def active_carts(self, request):
        """Get carts with items"""
        carts = Cart.objects.filter(items__isnull=False).distinct()
        serializer = self.get_serializer(carts, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')

        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            return Response({'status': 'updated'})

        return Response({'error': 'Invalid status'}, status=400)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(telegram_id__isnull=False)
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['patch'])
    def toggle_active(self, request, pk=None):
        """Toggle user active status"""
        user = self.get_object()
        user.is_active_telegram = not user.is_active_telegram
        user.save()
        return Response({'is_active': user.is_active_telegram})
