from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from apps.products.models import Category, Product, ProductColor, Cart, CartItem
from apps.orders.models import Order, STATUS_CHOICES
from .serializers import (
    CategorySerializer, ProductSerializer, CartSerializer,
    OrderSerializer, UserSerializer, CategoryCreateUpdateSerializer
)

User = get_user_model()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(parent__isnull=True).order_by('order', 'name')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]  # Only for admin panel

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateUpdateSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            CategorySerializer(serializer.instance, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(
            CategorySerializer(serializer.instance, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        category = self.get_object()
        children = category.subcategories.all().order_by('order', 'name')
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get full category tree"""
        root_categories = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(root_categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def flat(self, request):
        """Get all categories as a flat list with full path"""
        categories = Category.objects.all().order_by('order', 'name')
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def by_category(self, request):
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
        order = self.get_object()
        new_status = request.data.get('status')

        if new_status in dict(STATUS_CHOICES):
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
        user = self.get_object()
        user.is_active_telegram = not user.is_active_telegram
        user.save()
        return Response({'is_active': user.is_active_telegram})
