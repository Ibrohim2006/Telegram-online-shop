from decimal import Decimal
from django.db import models
from apps.users.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories',
                               verbose_name="Parent Category")
    category_image = models.ImageField(upload_to='categories/', null=True, blank=True, verbose_name="Category Image")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Display Order")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']
        db_table = 'category'

    def __str__(self):
        return self.full_path

    @property
    def full_path(self):
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.order or self.order == 0:
            max_order = Category.objects.aggregate(models.Max('order'))['order__max'] or 0
            self.order = max_order + 1
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Product Name")
    description = models.TextField(blank=True, verbose_name="Description")
    categories = models.ManyToManyField(Category, related_name='products', verbose_name="Categories")
    product_image = models.ImageField(upload_to='products/', verbose_name="Product Image")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        db_table = 'product'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def min_price(self):
        colors = self.colors.filter(is_active=True)
        return min((color.price for color in colors), default=0)


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors', verbose_name="Product")
    name = models.CharField(max_length=100, verbose_name="Color Name")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Product Color"
        verbose_name_plural = "Product Colors"
        db_table = 'product_color'
        ordering = ['name']

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductColorImage(models.Model):
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name='images',
                              verbose_name="Product Color")
    image = models.ImageField(upload_to='products/colors/', verbose_name="Image")
    order = models.PositiveIntegerField(default=0, verbose_name="Display Order")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Product Color Image"
        verbose_name_plural = "Product Color Images"
        ordering = ['order', 'id']
        db_table = 'product_color_image'

    def __str__(self):
        return f"{self.color} - Image {self.order}"

    def save(self, *args, **kwargs):
        if self.order == 0:
            last_order = ProductColorImage.objects.filter(color=self.color).aggregate(
                models.Max('order')
            )['order__max'] or 0
            self.order = last_order + 1
        super().save(*args, **kwargs)


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', verbose_name="User")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        db_table = 'cart'
        ordering = ['-created_at']

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_amount(self) -> float:
        items = self.items.all()
        return sum(item.total_price for item in items) if items.exists() else 0


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Cart")
    product_color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, verbose_name="Product Color")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        db_table = 'cart_item'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product_color'], name='unique_cart_product_color')
        ]

    def __str__(self):
        return f"{self.product_color} x {self.quantity}"

    @property
    def total_price(self) -> Decimal:
        return self.product_color.price * self.quantity
