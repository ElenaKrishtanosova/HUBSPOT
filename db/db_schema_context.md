# HubSpot CRM Database Schema Context

## Overview
This document describes the simplified HubSpot CRM database schema optimized for business insights generation and incremental data insertion.

## Schema Version
**Version:** 3.0  
**Last Updated:** August 2024  
**Description:** Simplified schema with BIGSERIAL IDs for incremental data insertion

## Core Tables

### 1. Companies
**Purpose:** Store company information and details

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `company_domain` | TEXT | PRIMARY KEY | Company domain (unique identifier) |
| `name` | TEXT | NOT NULL | Company name |
| `industry` | TEXT | CHECK constraint | Industry classification |

**Industry Constraints:**
- Retail
- Wholesale
- Manufacturing
- Distribution

### 2. Contacts
**Purpose:** Store contact person information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `contact_email` | TEXT | PRIMARY KEY | Contact email (unique identifier) |
| `first_name` | TEXT | - | Contact first name |
| `last_name` | TEXT | - | Contact last name |
| `company_domain` | TEXT | FK → companies.company_domain | Associated company |

### 3. Deals
**Purpose:** Store sales deals and opportunities

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `deal_id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing deal identifier |
| `deal_name` | TEXT | NOT NULL | Deal name |
| `deal_stage` | TEXT | CHECK constraint | Deal stage |
| `description` | TEXT | - | Deal description |
| `contact_email` | TEXT | FK → contacts.contact_email | Associated contact |
| `company_domain` | TEXT | FK → companies.company_domain | Associated company |
| `activity_date` | TIMESTAMPTZ | - | Activity timestamp |

**Deal Stage Constraints:**
- Appointment Scheduled
- Qualified to Buy
- Presentation Scheduled
- Closed Won
- Closed Lost

### 4. Tickets
**Purpose:** Store support tickets and issues

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `ticket_id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing ticket identifier |
| `ticket_name` | TEXT | NOT NULL | Ticket name |
| `priority` | TEXT | CHECK constraint | Priority level |
| `issue_of_interest` | TEXT | CHECK constraint | Issue type |
| `description` | TEXT | - | Ticket description |
| `contact_email` | TEXT | FK → contacts.contact_email | Associated contact |
| `company_domain` | TEXT | FK → companies.company_domain | Associated company |
| `ticket_owner` | TEXT | FK → users.email | Ticket owner email |
| `activity_date` | TIMESTAMPTZ | - | Activity timestamp |

**Priority Constraints:**
- Low
- Medium
- High

**Issue of Interest Constraints:**
- Crumb tray
- Overheating
- Wi‑Fi setup
- Shipping delay
- Thermostat
- Packaging
- Noise
- Invoice

### 5. Products
**Purpose:** Store product catalog information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `product_id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing product identifier |
| `name` | TEXT | NOT NULL UNIQUE | Product name |
| `description` | TEXT | - | Product description |
| `price` | NUMERIC(18,2) | - | Product price |

### 6. Users
**Purpose:** Store system users and owners

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing user identifier |
| `email` | TEXT | NOT NULL UNIQUE | User email |
| `full_name` | TEXT | - | User full name |

## Activity Tables

### 7. Tasks
**Purpose:** Task management and assignments

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `task_id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing task identifier |
| `title` | TEXT | NOT NULL | Task title |
| `notes` | TEXT | - | Task notes |
| `assigned_to_user_id` | BIGINT | FK → users.user_id | Assigned user |
| `deal_id` | BIGINT | FK → deals.deal_id | Associated deal |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Task creation timestamp |

### 8. Calls
**Purpose:** Call records and communications

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `call_id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing call identifier |
| `notes` | TEXT | - | Call notes |
| `direction` | TEXT | - | Inbound/Outbound |
| `assigned_to_user_id` | BIGINT | FK → users.user_id | Assigned user |
| `contact_email` | TEXT | FK → contacts.contact_email | Associated contact |
| `activity_at` | TIMESTAMPTZ | - | Call timestamp |

### 9. Emails
**Purpose:** Email communications

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `email_id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing email identifier |
| `body` | TEXT | - | Email body |
| `subject` | TEXT | - | Email subject |
| `contact_email` | TEXT | FK → contacts.contact_email | Associated contact |
| `direction` | TEXT | - | Incoming/Outgoing |
| `created_at` | TIMESTAMPTZ | - | Email creation timestamp |

### 10. Notes
**Purpose:** General notes and documentation

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `note_id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing note identifier |
| `body` | TEXT | NOT NULL | Note content |
| `activity_assigned_to_user_id` | BIGINT | FK → users.user_id | Assigned user |
| `contact_email` | TEXT | FK → contacts.contact_email | Associated contact |
| `deal_id` | BIGINT | FK → deals.deal_id | Associated deal |
| `ticket_id` | BIGINT | FK → tickets.ticket_id | Associated ticket |
| `activity_date` | TIMESTAMPTZ | - | Activity timestamp |

### 11. Deal Line Items
**Purpose:** Line items within deals

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `deal_id` | BIGINT | FK → deals.deal_id ON DELETE CASCADE | Associated deal |
| `product_id` | BIGINT | FK → products.product_id | Associated product |
| `quantity` | INTEGER | NOT NULL DEFAULT 1 | Quantity |
| `unit_price` | NUMERIC(18,2) | - | Unit price |

## Association Tables

### 12. Company-Contact Associations
**Purpose:** Many-to-many company-contact relationships

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `company_domain` | TEXT | FK → companies.company_domain ON DELETE CASCADE | Company domain |
| `contact_email` | TEXT | FK → contacts.contact_email ON DELETE CASCADE | Contact email |

**Primary Key:** `(company_domain, contact_email)`

### 13. Deal-Company Associations
**Purpose:** Many-to-many deal-company relationships

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `deal_id` | BIGINT | FK → deals.deal_id ON DELETE CASCADE | Deal identifier |
| `company_domain` | TEXT | FK → companies.company_domain ON DELETE CASCADE | Company domain |

**Primary Key:** `(deal_id, company_domain)`

## Key Changes in Version 3.0

### Schema Simplification
- **Removed:** Vector embeddings, complex fields, and unnecessary constraints
- **Simplified:** Association tables without labels
- **Streamlined:** Focus on essential fields for business insights

### ID Field Updates
- **All primary keys:** Now use BIGSERIAL for proper auto-increment functionality
- **Foreign keys:** Updated to reference BIGSERIAL fields
- **Benefits:** Enables incremental data insertion without ID conflicts

### Date Field Unification
- **All date fields:** Now use TIMESTAMPTZ for consistency
- **Benefits:** 
  - Standardized format across all tables
  - Better performance for time-based queries
  - Easier data export and import
  - Consistent timezone handling

### Field Consolidation
- **Companies:** Simplified to essential fields (domain, name, industry)
- **Contacts:** Streamlined structure with email as primary key
- **Deals/Tickets:** Focus on core business fields
- **Activities:** Essential tracking fields only

### Use Case Optimization
- **Business Insights:** Schema designed for pattern detection
- **Incremental Data:** Support for adding historical data
- **Performance:** Simplified structure for faster queries
- **Maintenance:** Easier to manage and update
- **Time-based Analysis:** Consistent timestamp format for all date fields

