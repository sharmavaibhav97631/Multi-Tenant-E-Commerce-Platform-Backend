Multi-Tenant E-Commerce Backend (Django + DRF + JWT)

A production-ready multi-tenant e-commerce backend where multiple vendors (tenants) can run their own online stores on a shared backend system.
Each vendor has isolated:

    Products
    Orders
    Staff users
    Customers

Tenant isolation is enforced using row-level multi-tenancy and JWT role-based permissions.

Features

Multi-Tenancy

    Each vendor (Tenant) has its own data.
    Data separation using FK → tenant.
    No user can access another tenant’s data.

Authentication & Authorization

    JWT Authentication (access + refresh tokens)
    Custom JWT payload includes:
        tenant_id
        user role (owner, staff, customer)
    Role-based access control:
        Owner: Full store control
        Staff: Manage products & orders
        Customer: View products, place orders, view own orders

E-Commerce Modules

    Product CRUD
    Customer order placement
    Order listing & management
    Auto-calculated pricing and totals

Tech Stack

    Django
    Django REST Framework
    SimpleJWT
    SQLite
    Python 3.12+

Project Folder Structure

multistore/
│
├── multistore/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── store/
│   ├── models.py          # Tenant, User, Product, Order, OrderItem
│   ├── serializers.py     # DRF serialization layer
│   ├── views.py           # API logic
│   ├── permissions.py     # Role-based + tenant-based access
│   ├── middleware.py      # request.tenant setter
│   ├── urls.py            # store API routes
│   ├── admin.py           # Django admin configuration
│   └── tests.py
│
└── manage.py


Installation Guide

1. Create Virtual Environment
python -m venv .venv
source .venv/bin/activate      # Linux
# .venv\Scripts\activate.bat   # Windows

2. Install Dependencies
pip install -r requirements.txt

3. Run Migrations
python manage.py makemigrations
python manage.py migrate

4. Create Superuser
python manage.py createsuperuser

5. Start Development Server
python manage.py runserver

Multi-Tenant Architecture Explained

How Tenancy Works
Every important model contains:

tenant = models.ForeignKey(Tenant, ...)

When a user logs in, JWT contains:

    {
    "user_id": 5,
    "tenant_id": 2,
    "role": "customer"
    }
    request.user.tenant is injected using middleware.

All queries automatically filter:
    Product.objects.filter(tenant=request.user.tenant)
This ensures tenant isolation.

User Roles & Permissions

Role	    Can_View_Products    Can_Create_Products    Can_Place_Order    Can_Manage+Orders
Owner	         YES	                YES         	       NO              	  NO
Staff	         YES                    NO     	               NO                 YES
Customer	     yes                    NO                     YES                NO

Authentication APIs

Register New User
POST /api/auth/register/
{
  "username": "owner1",
  "email": "owner1@acme.com",
  "password": "secretpass",
  "role": "owner",
  "tenant": 1
}

Login (JWT Token)

POST /api/auth/token/

{
  "refresh": "...",
  "access": "...",
  "role": "customer",
  "tenant_id": 2,
  "user_id": 6
}

Tenant APIs
Create Tenant

(Admin only by default)

POST /api/tenants/
curl -X POST http://127.0.0.1:8000/api/tenants/ \
-H "Authorization: Bearer <ADMIN_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "name": "Acme Store",
  "contact_email": "support@acme.com",
  "domain": "acme.local"
}'

Product APIs
Create Product (Owner / Staff)

curl -X POST http://127.0.0.1:8000/api/products/ \
-H "Authorization: Bearer <OWNER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "name": "T-Shirt",
  "description": "Premium cotton",
  "price": "299.99",
  "sku": "TSH-001"
}'

List Products (All authenticated roles)

curl -X GET http://127.0.0.1:8000/api/products/ \
-H "Authorization: Bearer <CUST_ACCESS_TOKEN>"

Order APIs
Customer Places Order

curl -X POST http://127.0.0.1:8000/api/orders/ \
-H "Authorization: Bearer <CUST_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "items": [
    {
      "product": 1,
      "quantity": 2
    }
  ]
}'

Backend automatically:

✔ Fills unit_price from product
✔ Calculates total_amount
✔ Assigns tenant from user

List Orders
Owner / Staff:

curl -X GET http://127.0.0.1:8000/api/orders/ \
-H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"

Customer (only own orders):

curl -X GET http://127.0.0.1:8000/api/orders/ \
-H "Authorization: Bearer <CUST_ACCESS_TOKEN>"

Update Order Status (Owner / Staff)

curl -X PATCH http://127.0.0.1:8000/api/orders/1/ \
-H "Authorization: Bearer <STAFF_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{"status": "processing"}'


Customer cannot update orders

Expected:
You do not have permission to perform this action.

Refresh Token

curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
-H "Content-Type: application/json" \
-d '{
  "refresh": "<REFRESH_TOKEN>"
}'



FULL MULTI-TENANT E-COMMERCE API TESTING — cURL COLLECTION

1. Create Tenant (via API as admin)
First login with superuser to get ADMIN_ACCESS_TOKEN

1.1 Admin Login

curl -X POST http://127.0.0.1:8000/api/auth/token/ \
-H "Content-Type: application/json" \
-d '{
  "username": "admin",
  "password": "<ADMIN_PASSWORD>"
}'

Copy the "access" token:

ADMIN_ACCESS_TOKEN=eyJhbGciOi...

1.2 Create Tenant

curl -X POST http://127.0.0.1:8000/api/tenants/ \
-H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "name": "Acme Store",
  "contact_email": "owner1@acme.com",
  "domain": "acme.local"
}'

You get:
{id: 1, name: "Acme Store", ...}
Your Tenant ID = 1

2. Register Owner User

curl -X POST http://127.0.0.1:8000/api/auth/register/ \
-H "Content-Type: application/json" \
-d '{
  "username": "owner1",
  "email": "owner1@acme.com",
  "password": "secretpass",
  "role": "owner",
  "tenant": 1
}'


3. Owner Login → Get OWNER_ACCESS_TOKEN

curl -X POST http://127.0.0.1:8000/api/auth/token/ \
-H "Content-Type: application/json" \
-d '{
  "username": "owner1",
  "password": "secretpass"
}'

OWNER_ACCESS_TOKEN=eyJhbGc...


4. Register Staff User

curl -X POST http://127.0.0.1:8000/api/auth/register/ \
-H "Content-Type: application/json" \
-d '{
  "username": "staff1",
  "email": "staff1@acme.com",
  "password": "staffpass",
  "role": "staff",
  "tenant": 1
}'


5. Staff Login → STAFF_ACCESS_TOKEN

curl -X POST http://127.0.0.1:8000/api/auth/token/ \
-H "Content-Type: application/json" \
-d '{
  "username": "staff1",
  "password": "staffpass"
}'

STAFF_ACCESS_TOKEN=eyJhbGc...

6. Register Customer User
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
-H "Content-Type: application/json" \
-d '{
  "username": "cust1",
  "email": "cust1@acme.com",
  "password": "custpass",
  "role": "customer",
  "tenant": 1
}'

7. Customer Login → CUST_ACCESS_TOKEN

curl -X POST http://127.0.0.1:8000/api/auth/token/ \
-H "Content-Type: application/json" \
-d '{
  "username": "cust1",
  "password": "custpass"
}'

CUST_ACCESS_TOKEN=eyJhbGc...

PRODUCT APIs
8. Create Product (Owner only or Staff)
curl -X POST http://127.0.0.1:8000/api/products/ \
-H "Authorization: Bearer <OWNER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "name": "T-Shirt",
  "description": "Premium cotton",
  "price": "299.99",
  "sku": "TSHIRT-001"
}'

9. List Products (Anyone inside tenant)
Owner:
curl -X GET http://127.0.0.1:8000/api/products/ \
-H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"

Customer:

curl -X GET http://127.0.0.1:8000/api/products/ \
-H "Authorization: Bearer <CUST_ACCESS_TOKEN>"


ORDER APIs
(Customer places order)

10. Place Order (Customer)

curl -X POST http://127.0.0.1:8000/api/orders/ \
-H "Authorization: Bearer <CUST_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "items": [
    {
      "product": 1,
      "quantity": 2
    }
  ]
}'

11. List Orders
Customer (Own Orders Only):
curl -X GET http://127.0.0.1:8000/api/orders/ \
-H "Authorization: Bearer <CUST_ACCESS_TOKEN>"

Owner:
curl -X GET http://127.0.0.1:8000/api/orders/ \
-H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"

12. View Single Order
curl -X GET http://127.0.0.1:8000/api/orders/1/ \
-H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"

Customer:
curl -X GET http://127.0.0.1:8000/api/orders/1/ \
-H "Authorization: Bearer <CUST_ACCESS_TOKEN>"

13. Update Order Status (Owner or Staff)

curl -X PATCH http://127.0.0.1:8000/api/orders/1/ \
-H "Authorization: Bearer <STAFF_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{"status": "processing"}'

14. Customer cannot update orders (Forbidden)

curl -X PATCH http://127.0.0.1:8000/api/orders/1/ \
-H "Authorization: Bearer <CUST_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{"status": "completed"}'

Expected:
"You do not have permission..."

15. Refresh Token

curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
-H "Content-Type: application/json" \
-d '{
  "refresh": "<REFRESH_TOKEN_FROM_LOGIN>"
}'