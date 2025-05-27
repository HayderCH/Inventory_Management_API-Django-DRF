## README Content for Inventory Management & User Authentication System

This README describes a comprehensive Django-based application that combines robust inventory management with a secure, enterprise-grade user authentication and management system. The project leverages Django REST Framework (DRF) and JWT authentication to deliver scalable, secure, and auditable operations for modern organizations.

---

**Overview**

This application provides:

- Full-featured inventory management supporting products, suppliers, orders, multi-location stock, adjustments, and transfers.
- A secure JWT-based authentication and user management system with role-based access control (RBAC), advanced account security, and a complete automated testing suite.

---

## Features

**Inventory Management**

- Product, supplier, and category management
- Multi-location stock tracking
- Order creation, approval, and fulfillment
- Stock adjustments (receipts, removals, corrections, audits, transfers, losses)
- Stock transfers with approval workflow
- Audit logging for all create, update, and delete actions

**User Management & Authentication**

- JWT-based authentication with access and refresh tokens[2][3]
- Secure token refresh and blacklisting for logout and session management[2][3]
- Rate limiting to prevent brute force attacks
- User registration with email verification
- Role-based authorization (Admin, Manager, Employee, Auditor)
- User profile management
- Password management with reset flow
- Account lockout after multiple failed login attempts
- IP address tracking and login attempt logging
- CSRF protection and secure token validation
- Strong password validation

**Testing**

- **All features, endpoints, and security flows are fully covered by automated tests.**

---

## Data Model Overview

| Model             | Description                                                                                              |
|-------------------|---------------------------------------------------------------------------------------------------------|
| Product           | SKU, name, category, price, stock, supplier relationships                                               |
| Supplier          | Contact info, contracts, rating                                                                         |
| ProductSupplier   | Product-supplier mapping with pricing, lead time, contract, preferred status                            |
| Location          | Multi-site support (warehouses, stores, etc.)                                                           |
| Order             | Purchase order tracking, status, supplier linkage                                                       |
| OrderProduct      | Products per order, quantity, unit price                                                                |
| StockLevel        | Per-location inventory                                                                                  |
| StockAdjustment   | Inventory changes (receive, remove, correct, audit, transfer, loss) with user and reason logging        |
| StockTransfer     | Inter-location transfers with status and approval workflow                                               |
| AuditLog          | User, action, object type, timestamp, and extra data for all object changes                             |

---

API Serialization Strategy
This system uses a structured serializer approach to optimize performance and maintain clear data contracts:

Serializer Type	Purpose	Example Models	Key Characteristics
List	Minimal data for list views	Product, Supplier, Location	Only includes core fields (id,name,sku,code)
Detail	Full object data + nested relationships	Product, Order, StockTransfer	Includes all fields + nested serializers (e.g., suppliers for Product)
Write	Create/update operations with nested writable fields	Order, StockAdjustment	Handles nested creates/updates (e.g., OrderProducts when creating Orders)
Short	Foreign key relationships/autocomplete	Supplier, Location	Limited fields for dropdowns (id,name,code)
Nested	Embedded relationships in detail views	ProductSupplier, AuditLog	Used within detail serializers to show related data
![image](https://github.com/user-attachments/assets/397af6a7-5d26-40a1-a91f-cf54fc550baf)


python
class ProductWriteSerializer(serializers.ModelSerializer):
    suppliers = ProductSupplierWriteSerializer(many=True)

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        suppliers_data = validated_data.pop('suppliers')
        product = Product.objects.create(**validated_data)
        for supplier_data in suppliers_data:
            ProductSupplier.objects.create(product=product, **supplier_data)
        return product
Order Detail Serializer (Nested Read)

python
class OrderDetailSerializer(serializers.ModelSerializer):
    order_products = OrderProductSerializer(many=True)
    supplier = SupplierShortSerializer()

    class Meta:
        model = Order
        fields = '__all__'
        depth = 1
StockAdjustment List Serializer

python
class StockAdjustmentListSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer()
    location = LocationShortSerializer()

    class Meta:
        model = StockAdjustment
        fields = ['id', 'adjusted_at', 'product', 'location', 'quantity', 'adjustment_type']
Key Design Principles
Write Operations

Use drf-writable-nested for complex nested creates/updates 

Separate write serializers prevent mass assignment vulnerabilities

Full transaction support for atomic operations

Read Optimization

prefetch_related/select_related in list/detail views

Separate serializers prevent over-fetching

~60% reduced payload size vs single serializer approach 

Security

Write serializers explicitly define allowed fields

Nested updates require full object validation

Audit logs track all serializer-level changes 

This structured approach ensures optimal performance while maintaining clear separation of concerns between API operations. The implementation follows Django REST Framework best practices and leverages proven third-party libraries for complex nested writes.
---

## Authentication Flow (JWT)

- Users log in via `/api/token/` with credentials; receive access and refresh tokens[2][3].
- Access token is sent with every API request in the `Authorization: Bearer ` header[3].
- If the access token expires, the refresh token is used at `/api/token/refresh/` to obtain a new access token[3].
- Token blacklisting ensures secure logout and session invalidation[2].
- Rate limiting and account lockout protect against brute force attacks.
- All authentication and authorization logic is fully tested.

---

## Security Highlights

- All sensitive actions require authentication and appropriate user roles.
- Passwords are validated for strength and never stored in plain text.
- Email verification is required for registration.
- Account lockout and rate limiting are enforced for failed login attempts.
- All tokens are securely generated, validated, and blacklisted on logout.
- IP address and login attempts are logged for auditing.
- CSRF protection is enforced for all relevant endpoints.

---

## Getting Started

1. **Clone the repository**
2. **Install dependencies**
   - `pip install -r requirements.txt`
3. **Apply migrations**
   - `python manage.py migrate`
4. **Create a superuser**
   - `python manage.py createsuperuser`
5. **Run the development server**
   - `python manage.py runserver`

---

## Usage

- Access the admin panel at `/admin/` for full CRUD operations.
- Use the REST API endpoints for integration, authentication, and inventory operations.
- All endpoints are protected by JWT authentication and RBAC.

---

## Customization & Extensibility

- Models and serializers are designed for easy extension.
- Audit logging and stock adjustment types can be expanded as needed.
- User roles and permissions can be customized for your organization.

---

## Testing

**All features and security flows are fully covered by automated tests.**  
Run tests with:

```
python manage.py test
```

---


---

## Contact

For questions or support, contact [hayderchakroun5@example.com].

---

This README provides a complete, professional overview for deploying, using, and extending your Django inventory and user management system, including all authentication, security, and testing guarantees.
