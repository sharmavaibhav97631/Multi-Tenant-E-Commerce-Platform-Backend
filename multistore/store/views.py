# store/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Tenant, Product, Order, OrderItem
from .serializers import (
    TenantSerializer, ProductSerializer, OrderSerializer,
    UserRegisterSerializer, CustomTokenObtainPairSerializer
)
# IMPORTANT: import the updated permission class name
from .permissions import IsTenantMember, IsOwner, ProductOrderPermission
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


# Auth endpoints
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    Register an user. To create a new Tenant and Owner, create tenant first then register user with role=owner and tenant=<id>.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer


# Tenants list (admin use)
class TenantViewSet(viewsets.ModelViewSet):
    """
    Allow listing/creating/updating tenants via API.
    Restrict creation to superusers/admins (or change permission as needed).
    """
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]  # adjust if you want admin-only


# Base mixin for tenant filtering
class TenantQuerysetMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        request = self.request
        tenant = getattr(request, "tenant", None)
        if tenant:
            return qs.filter(tenant=tenant)
        # if no tenant, return empty queryset to avoid leakage
        return qs.none()


class ProductViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    """
    Products are tenant-scoped. Owners & Staff can manage. Customers can read.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, ProductOrderPermission]

    def perform_create(self, serializer):
        # automatically assign tenant from request.user
        tenant = getattr(self.request.user, "tenant", None)
        serializer.save(tenant=tenant)


class OrderViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    """
    Orders: customers can create (POST) their own orders.
    Owner/Staff can manage orders of their tenant.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, ProductOrderPermission]

    def perform_create(self, serializer):
        # Force tenant and customer from the authenticated user (do NOT trust incoming tenant/customer)
        tenant = getattr(self.request.user, "tenant", None)
        serializer.save(tenant=tenant, customer=self.request.user)
