# Inventory & Supply Chain Management API  
*Technical Documentation*

---

## 1. Executive Summary

This document details the initial design and implementation of the Inventory & Supply Chain Management API. The system targets enterprise-grade inventory tracking, supplier management, purchase orders, and multi-site stock control. The aim is to provide robust auditability, flexible supplier-product relationships, and role-based access control, all built with Django and PostgreSQL.

---

## 2. System Architecture

- **Backend Framework:** Django 5.x with Django REST Framework (DRF)
- **Database:** PostgreSQL
- **Authentication:** Role-based (planned: admin, manager, staff, viewer)
- **Key Modules So Far:**  
  - Product Management  
  - Supplier Management  
  - Product-Supplier Relationship  
  - Foundation for Order and Stock Management

---

## 3. Data Model

See [`docs/data-model.md`](./data-model.md) for the in-depth specification.

**Key Entities Implemented:**
- **Product:** Tracks inventory items, details, category, price, current/minimum stock.
- **Supplier:** Stores supplier business/contact info, contract, rating, etc.
- **ProductSupplier:** Through table linking Product & Supplier, storing supplier-specific pricing, lead time, contract info, and preference.

**Entity Relationships:**
- Products and Suppliers are linked via a Many-to-Many relationship using the `ProductSupplier` model, which stores additional metadata about each supplier-product pairing.

---

## 4. Implementation Progress

### 4.1 Models

- All core models for Product, Supplier, and ProductSupplier have been defined in `inventory/models.py`.
- The `ProductSupplier` model uses `on_delete=CASCADE` for both foreign keys. If a product or supplier is removed, associated links are deleted, but the other side remains unchanged.
- Extra fields in `ProductSupplier` (e.g., `supplier_price`, `lead_time_days`) allow tracking differences per supplier.

### 4.2 Admin Integration

- All implemented models are registered in Django admin for CRUD operations and testing.
- String representations (`__str__`) are tailored for clarity in listings.

### 4.3 Migrations

- Database migrations have been created and applied.
- Confirmed PostgreSQL integration and successful table creation.

---

## 5. Technical Decisions & Rationale

- **Single App Structure:**  
  All inventory-related logic resides in one Django app (`inventory`) for simplicity and maintainability at this stage. Modularization will be considered as the project grows.
- **Through Table:**  
  `ProductSupplier` enables rich supplier-product linkage, matching business requirements for varying prices, lead times, and preferred suppliers.
- **Integrity:**  
  Use of `unique_together` ensures only one record per product-supplier pair.
- **No Cascade Beyond Relationship:**  
  Deletion cascades only to the linking table (`ProductSupplier`), never deleting products when suppliers are removed or vice versa.
- **Extensibility:**  
  Models are designed to be extended, with optional fields and clear separation for future modules (orders, stock, users, locations).

---

## 6. Setup & Validation

Current validated steps:
1. **Project & Virtual Environment:** Django project and virtualenv initialized.
2. **Database Driver:** psycopg2-binary installed and verified with PostgreSQL 16.
3. **Migrations:** Models migrated successfully, schema matches design.
4. **Admin:** Admin interface tested for data entry and relationship management.

---

## 7. Next Steps

- Complete implementation of the remaining core models: Order, Location, StockLevel, StockAdjustment, StockTransfer, and User (custom roles).
- Begin designing API endpoints using Django REST Framework for CRUD and workflow automation.
- Introduce unit tests for implemented models.
- Update this report as new modules are added.

---

## 8. Appendix

- [`docs/data-model.md`](./data-model.md): Comprehensive data model reference.
- ERD: *(To be generated; see data model for guidance.)*

---

*Prepared by: HayderCH, 2025-05-21*