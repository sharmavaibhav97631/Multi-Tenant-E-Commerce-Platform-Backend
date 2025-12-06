# store/permissions.py

from rest_framework import permissions

class IsTenantMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.tenant)

class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == request.user.ROLE_OWNER)


class ProductOrderPermission(permissions.BasePermission):
    """
    Generic permission for Products and Orders:
    - Owner: full access within tenant
    - Staff: full access within tenant (can create/update products & orders)
    - Customer: can read products and can CREATE orders (POST) for their tenant, and read their own orders.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Owners and staff can do anything (subject to tenant-check later)
        if user.role in (user.ROLE_OWNER, user.ROLE_STAFF):
            return True

        # Customers:
        if user.role == user.ROLE_CUSTOMER:
            # allow read-only on list/detail of products/orders
            if request.method in permissions.SAFE_METHODS:
                return True
            # allow creating orders (POST) — but not updating/deleting
            if view.basename == "order" and request.method == "POST":
                return True
            # customers cannot create/update products
            return False

        return False

    def has_object_permission(self, request, view, obj):
        """
        Object-level check: ensure object belongs to user's tenant.
        - For Orders: owners/staff allowed; customers allowed only to access their own orders.
        - For Products: owner/staff allowed; customers only read.
        """
        user = request.user
        if not user or not user.tenant:
            return False

        # ensure tenant matches
        obj_tenant = getattr(obj, "tenant", None)
        if obj_tenant != user.tenant:
            return False

        if user.role in (user.ROLE_OWNER, user.ROLE_STAFF):
            return True

        if user.role == user.ROLE_CUSTOMER:
            # For Orders: allow if this customer owns the order
            if hasattr(obj, "customer"):
                return obj.customer == user
            # For Product: customer read-only already handled by has_permission SAFE_METHODS
            return request.method in permissions.SAFE_METHODS

        return False
