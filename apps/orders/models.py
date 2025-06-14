from django.db import models
from apps.products.models import ProductColor
from apps.users.models import User
from apps.users.utils import validate_phone_number

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
]


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="User")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Order Status")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Amount")
    phone_number = models.CharField(max_length=13, validators=[validate_phone_number], verbose_name="Phone Number")
    address = models.TextField(verbose_name="Delivery Address")
    notes = models.TextField(blank=True, verbose_name="Notes")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'order'
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Order")
    product_color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, verbose_name="Product Color")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Unit Price")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'order_item'
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product_color} x {self.quantity}"

    @property
    def total_price(self):
        return self.price * self.quantity
