# store/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Tenant, Product, Order, OrderItem

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Add tenant_id and role in access token payload (and in response).
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims
        token["role"] = user.role
        token["tenant_id"] = user.tenant.id if user.tenant else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["tenant_id"] = self.user.tenant.id if self.user.tenant else None
        data["user_id"] = self.user.id
        data["username"] = self.user.username
        return data


# Serializers for API resources

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "contact_email", "domain", "created_at"]


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, required=True)
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all(), required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role", "tenant"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "tenant", "name", "description", "price", "sku", "is_active", "created_at"]
        read_only_fields = ["tenant", "created_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    product_detail = ProductSerializer(source="product", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_detail", "quantity", "unit_price"]
        read_only_fields = ["unit_price"]   # IMPORTANT FIX



class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "tenant", "customer", "customer_detail", "total_amount", "status", "placed_at", "items"]
        read_only_fields = ["tenant", "total_amount", "placed_at"]

    def get_customer_detail(self, obj):
        if obj.customer:
            return {"id": obj.customer.id, "username": obj.customer.username}
        return None

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context.get("request")
        tenant = getattr(request.user, "tenant", None)
        if tenant is None:
            raise serializers.ValidationError("User has no tenant associated.")

        # create order with tenant & customer from request
        order = Order.objects.create(tenant=tenant, customer=request.user)
        total = 0
        for it in items_data:
            product = it.get("product")
            if product is None:
                order.delete()
                raise serializers.ValidationError("Each item must include a product id.")
            # ensure product belongs to same tenant
            if product.tenant != tenant:
                order.delete()
                raise serializers.ValidationError(f"Product {product.id} does not belong to your tenant.")
            qty = it.get("quantity", 1)
            unit_price = product.price
            OrderItem.objects.create(order=order, product=product, quantity=qty, unit_price=unit_price)
            total += unit_price * qty

        order.total_amount = total
        order.save()
        return order

