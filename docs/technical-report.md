# Inventory & Supply Chain Management API  
*Technical Progress Report Update*

---

## 1. Executive Summary

This document details the current design and implementation progress of the Inventory & Supply Chain Management API. The project leverages Django and PostgreSQL for robust inventory, supplier, order, and stock management in multi-site enterprise environments.

---

## 2. System Architecture

- **Backend:** Django 5.x with Django REST Framework (to be implemented)
- **Database:** PostgreSQL
- **Authentication:** Planned (Django User, role-based)
- **Key Modules:**  
  - Product Management  
  - Supplier Management  
  - Product-Supplier Relationship  
  - Location Management  
  - Order & Order Line Items  
  - Stock Levels & Adjustments  
  - Stock Transfers

---

## 3. Data Model

### **Entities Implemented:**
- **Product:** SKU, description, category, price, current/minimum stock.
- **Supplier:** Contact info, address, contract details, rating, notes.
- **ProductSupplier:** Through table for product-supplier M2M with supplier-specific details (price, SKU, lead time, contract, preferred flag).
- **Location:** Warehouses/stores with code, address, notes.
- **Order:** Purchase orders, status, supplier, timestamps.
- **OrderProduct:** Line items (product, quantity, price) linked to Orders.
- **StockLevel:** Quantity of each product at each location (unique per product/location).
- **StockAdjustment:** Audit trail for every stock change, including transfers, receipts, corrections, losses, and audits.
- **StockTransfer:** Tracks inter-location product movements, including status, source/destination, and approval.

---

## 4. Implementation Progress

### **Model Layer**
- All core models above have been implemented in `inventory/models.py` using Django best practices.
- Correct usage of `on_delete` behaviors (`CASCADE`, `PROTECT`, `SET_NULL`) to ensure referential integrity and prevent data loss.
- Optional fields are handled with `blank=True` and, for non-string types, `null=True` (per Django convention).
- All `CharField`/`TextField` optionals use `blank=True` only (no unnecessary `null=True`).
- All models have meaningful `__str__` methods for admin/debugging.

### **Migration Layer**
- Ran `python manage.py makemigrations inventory` and `python manage.py migrate` successfully.
- All database tables created and schema validated.
- Legacy data issues (e.g., non-nullable field changes) were handled by keeping optional fields nullable as appropriate.

### **Admin Layer**
- (Pending) To be registered in `admin.py` for easy management.

---

## 5. Technical Decisions & Rationale

- **Referential Integrity:**  
  - `PROTECT` for critical linked data (e.g. Orders cannot have their Supplier quietly deleted).
  - `CASCADE` for dependent data (e.g. deleting a Product deletes its StockLevels).
- **Optional Field Handling:**  
  - Used `blank=True, null=True` on non-string fields (dates, FKs) where optional.
  - Used `blank=True` only for optional strings, as per Django best practice.
- **Data Consistency:**  
  - Enforced uniqueness on composite keys (e.g. Product+Location in StockLevel).
- **Documentation:**  
  - Kept this technical report and `docs/data-model.md` up to date for each stage.

---

## 6. Next Steps

- Register all models in `inventory/admin.py` for admin CRUD.
- Begin implementation of API layer using Django REST Framework (serializers, viewsets, endpoints).
- Plan and implement role-based permissions and authentication.
- Add unit tests for model and API validation.

---

*Updated: 2025-05-21 by HayderCH*