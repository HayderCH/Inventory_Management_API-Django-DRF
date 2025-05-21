# DRF Serializers Plan for Inventory/Stock Management System

## 1. Why Serializers?
Serializers "translate" between Django models (Python objects) and JSON (API data).  
They define what data is exposed, how it's structured, and what can be written/read by API clients.

---

## 2. Who Are Our Clients?

- **Frontend web apps** (React, Vue, etc.)
- **Mobile apps**
- **Internal tools** (dashboards, other services)
- **External partners** (vendors, suppliers)
- **Automations/Integrations**
- **API explorers/Postman**
- **IoT devices**
- **Public/third-party API users** (if applicable)

---

## 3. Roles & Permissions

| Role                | Needs / Use Cases                                           | Serializer/Permission Strategy                                    |
|---------------------|------------------------------------------------------------|-------------------------------------------------------------------|
| Warehouse Staff     | See products, update stock, transfer, see locations        | List/detail serializers (limited fields); write serializers for stock/transfer, limited to own location |
| Warehouse Manager   | All staff actions + approve transfers, adjust stock        | All staff serializers + admin/write serializers for approval, extended fields |
| Procurement         | List/create/update orders, browse suppliers/products       | Order serializers, supplier/product detail serializers, own orders only |
| Supplier            | (If external API) See their own products/orders            | Public/limited serializers, restricted data                        |
| Admin               | Everything, all CRUD, audit logs                           | Full/unrestricted serializers, admin permissions                   |
| Auditor             | Read-only, history/audit                                   | Read-only/history serializers, all fields                          |
| API Integrator      | Automated scripts, IoT, etc.                               | Scoped/custom permissions                                          |

---

## 4. Serializer Types Per Model

| Model           | List  | Detail | Write | Admin | Public | Nested                  |
|-----------------|-------|--------|-------|-------|--------|-------------------------|
| Product         | ✓     | ✓      | ✓     | ✓     | ✓      | Suppliers (in detail)   |
| Supplier        | ✓     | ✓      | ✓     | ✓     | ✓      | -                       |
| Order           | ✓     | ✓      | ✓     | ✓     | -      | OrderProducts           |
| OrderProduct    | -     | -      | -     | -     | -      | Used as nested          |
| StockLevel      | ✓     | ✓      | -     | ✓     | -      | Product/location        |
| StockAdjustment | ✓     | ✓      | ✓     | ✓     | -      | -                       |
| StockTransfer   | ✓     | ✓      | ✓     | ✓     | -      | Locations               |

---

### **Example Serializers for Each Model**

#### Product
- `ProductListSerializer` (minimal fields for lists)
- `ProductDetailSerializer` (all fields, nested suppliers)
- `ProductWriteSerializer` (fields for create/update)
- `ProductAdminSerializer` (extra admin fields, e.g., audit info)

#### Supplier
- `SupplierListSerializer`
- `SupplierDetailSerializer`
- `SupplierWriteSerializer`
- `SupplierPublicSerializer` (if exposing to external suppliers)

#### Order
- `OrderListSerializer` (summary)
- `OrderDetailSerializer` (nested items, full info)
- `OrderWriteSerializer` (create/update, validation)
- `OrderAdminSerializer` (admin-only fields)

#### OrderProduct (Line items)
- `OrderProductSerializer` (nested use in Order serializers, read-only)

#### StockLevel
- `StockLevelSerializer` (for staff/manager, limited fields)
- `StockLevelDetailSerializer` (all locations, for managers/admin)

#### StockAdjustment
- `StockAdjustmentSerializer` (write: for adjustment, read: for audit/history)

#### StockTransfer
- `StockTransferListSerializer` (minimal)
- `StockTransferDetailSerializer` (full, nested locations)
- `StockTransferWriteSerializer` (for creation/approval)

---

## 5. How These Serializers Are Used

- **ViewSets** select the serializer per action/role using `get_serializer_class`.
- **Permissions** restrict who can use which endpoints/fields.
- **Nested serializers** for related data (e.g., Order with OrderProducts).
- **Read vs. write serializers**: expose only what's needed.
- **Custom validation**: enforce business rules (e.g., stock can't go negative).
- **Performance**: use minimal serializers for lists, detailed for detail views.
- **Security**: only expose safe fields in public/external serializers.

---

## 6. Tips for Implementation

- Start with Product and Order models for initial serializers.
- Use DRF’s `read_only_fields`, `write_only_fields` for fine-grained control.
- Use `fields = "__all__"` only where safe.
- Adjust/extend as you identify new use cases or expand API.

---

**This plan is your reference for structuring and expanding your serializers as your project grows.**