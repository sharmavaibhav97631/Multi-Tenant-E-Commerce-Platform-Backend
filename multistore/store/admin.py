# store/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tenant, User, Product, Order, OrderItem

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "contact_email", "domain", "created_at")


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Tenant & Role", {"fields": ("tenant", "role")}),
    )

admin.site.register(User, UserAdmin)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "tenant", "price", "is_active")
    list_filter = ("tenant", "is_active")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ("product", "quantity", "unit_price")
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "customer", "total_amount", "status", "placed_at")
    list_filter = ("tenant", "status")
    inlines = [OrderItemInline]
