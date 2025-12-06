# store/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Tenant(models.Model):
    """
    Vendor / Store
    """
    name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    domain = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.domain})" if self.domain else self.name


class User(AbstractUser):
    """
    Custom user with tenant and role.
    Roles: owner, staff, customer
    """
    ROLE_OWNER = "owner"
    ROLE_STAFF = "staff"
    ROLE_CUSTOMER = "customer"
    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_STAFF, "Staff"),
        (ROLE_CUSTOMER, "Customer"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users", null=True, blank=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Product(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.tenant.name}"


class Order(models.Model):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELED = "canceled"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
        (CANCELED, "Canceled"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="orders")
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=PENDING)
    placed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order #{self.id} ({self.tenant.name})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
