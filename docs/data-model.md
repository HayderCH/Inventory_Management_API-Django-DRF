# Data Model (WIP): Inventory & Supply Chain API

---

## Product

| Field           | Type      | Notes                                      |
|-----------------|-----------|--------------------------------------------|
| id              | Integer   | Primary Key (auto-increment, Django default) |
| name            | String    | Product name                               |
| sku             | String    | Unique Stock Keeping Unit                  |
| description     | Text      | Product details                            |
| category        | String    | Category name (e.g. "Laptops")             |
| price           | Decimal   | Cost per unit                              |
| current_stock   | Integer   | Current inventory level                    |
| minimum_stock   | Integer   | Minimum before reorder alert               |
| suppliers       | M2M       | ManyToMany with Supplier via ProductSupplier|
| created_at      | DateTime  | Auto — when product added                  |
| updated_at      | DateTime  | Auto — when product updated                |

---

## ProductSupplier (Through Model)

| Field           | Type      | Notes                                              |
|-----------------|-----------|----------------------------------------------------|
| id              | Integer   | Primary Key                                        |
| product         | FK        | ForeignKey to Product                              |
| supplier        | FK        | ForeignKey to Supplier                             |
| supplier_sku    | String    | Supplier's code for this product                   |
| supplier_price  | Decimal   | Price from this supplier                           |
| lead_time_days  | Integer   | Expected delivery time in days                     |
| contract_start  | Date      | When this supplier started supplying this product  |
| contract_end    | Date      | When supply contract ends                          |
| is_preferred    | Boolean   | Is this the preferred supplier?                    |
| UNIQUE(product, supplier)   | Ensures one row per product+supplier pair          |

---

## Supplier

| Field         | Type      | Notes                                                    |
|---------------|-----------|----------------------------------------------------------|
| id            | Integer   | Primary key (auto-increment, Django default)             |
| name          | String    | Supplier’s business name                                 |
| contact_name  | String    | Main contact person’s name                               |
| contact_email | String    | Contact email                                            |
| contact_phone | String    | Contact phone number (optional)                          |
| address       | String    | Physical address                                         |
| city          | String    | City                                                     |
| country       | String    | Country                                                  |
| rating        | Integer   | Internal supplier score (1-5 or 1-10)                    |
| contract_start| Date      | Start date of active contract (optional)                 |
| contract_end  | Date      | End date of contract (optional)                          |
| notes         | Text      | Freeform notes                                           |
| created_at    | DateTime  | Auto — when supplier added                               |
| updated_at    | DateTime  | Auto — when supplier updated                             |

---

## Order

| Field         | Type      | Notes                                                 |
|---------------|-----------|------------------------------------------------------|
| id            | Integer   | Primary key (auto-increment)                         |
| order_number  | String    | Unique order identifier                              |
| supplier      | FK        | ForeignKey to Supplier                               |
| status        | String    | pending/approved/shipped/received/canceled           |
| created_at    | DateTime  | When order created                                   |
| updated_at    | DateTime  | When order updated                                   |

---

## OrderProduct (Through Model)

| Field         | Type      | Notes                                                |
|---------------|-----------|------------------------------------------------------|
| id            | Integer   | Primary key                                          |
| order         | FK        | ForeignKey to Order                                  |
| product       | FK        | ForeignKey to Product                                |
| quantity      | Integer   | Number of items ordered                              |
| unit_price    | Decimal   | Price per item at time of order                      |

---
## StockAdjustment (with Transfer Reference)

| Field           | Type      | Notes                                                    |
|-----------------|-----------|----------------------------------------------------------|
| id              | Integer   | Primary key                                              |
| product         | FK        | Product                                                  |
| location        | FK        | Location (from or to)                                    |
| quantity        | Integer   | Positive (in) or negative (out) adjustment               |
| adjustment_type | String    | receive, remove, correct, audit, loss, transfer_in, transfer_out |
| reason          | String    | Short explanation                                        |
| stock_transfer  | FK        | StockTransfer (nullable, only for transfers)             |
| adjusted_by     | FK        | User (who made the change)                               |
| created_at      | DateTime  | When adjustment was made                                 |

## User

| Field        | Type      | Notes                                              |
|--------------|-----------|----------------------------------------------------|
| id           | Integer   | Primary key (auto-increment)                       |
| username     | String    | Unique login name                                  |
| email        | String    | Unique, for communication/reset                    |
| full_name    | String    | For display                                        |
| role         | String    | admin, manager, staff, viewer                      |
| is_active    | Boolean   | Can log in? (deactivate without delete)            |
| created_at   | DateTime  | When user was created                              |
| updated_at   | DateTime  | When user was updated                              |

## Location

| Field        | Type      | Notes                                                  |
|--------------|-----------|--------------------------------------------------------|
| id           | Integer   | Primary key                                            |
| name         | String    | Location name (“Main Warehouse”, “Store #3”, etc.)     |
| code         | String    | Unique code for quick reference/integration            |
| address      | String    | Physical address (optional)                            |
| city         | String    | City (optional)                                        |
| country      | String    | Country (optional)                                     |
| notes        | Text      | Freeform notes                                         |
| created_at   | DateTime  | When added                                             |
| updated_at   | DateTime  | When updated                                           |

---

## StockLevel

| Field        | Type      | Notes                                                  |
|--------------|-----------|--------------------------------------------------------|
| id           | Integer   | Primary key                                            |
| product      | FK        | Product                                                |
| location     | FK        | Location                                               |
| quantity     | Integer   | Current stock at this location                         |
| updated_at   | DateTime  | Last updated                                           |

---
## StockTransfer

| Field          | Type      | Notes                                                      |
|----------------|-----------|------------------------------------------------------------|
| id             | Integer   | Primary key                                                |
| product        | FK        | Product being transferred                                  |
| from_location  | FK        | Location stock is moving from                              |
| to_location    | FK        | Location stock is moving to                                |
| quantity       | Integer   | Amount transferred                                         |
| status         | String    | pending/approved/completed/canceled                        |
| reason         | String    | Why the transfer (“restock store”, “balance inventory”)    |
| requested_by   | FK        | User who initiated the transfer                            |
| approved_by    | FK        | User who approved (optional)                               |
| created_at     | DateTime  | When transfer was created                                  |
| updated_at     | DateTime  | When transfer was last updated                             |

---