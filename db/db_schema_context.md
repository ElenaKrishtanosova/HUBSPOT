# HubSpot CRM Database Schema Context

## Overview
This document describes the updated HubSpot CRM database schema with new field names and structure for better data organization and consistency.

## Schema Version
**Version:** 2.0  
**Last Updated:** December 2024  
**Description:** Major schema update with field renames and new constraints

## Core Tables

### 1. Companies
**Purpose:** Store company information and details

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `company_id` | BIGSERIAL | PRIMARY KEY | Unique company identifier |
| `name` | TEXT | NOT NULL | Company name |
| `company_domain` | TEXT | UNIQUE | Company domain (FK for associations) |
| `phone` | TEXT | - | Phone number (+[countrycode][digits]) |
| `city` | TEXT | - | Company city |
| `industry` | TEXT | CHECK constraint | Industry classification |
| `number_of_employees` | INTEGER | - | Employee count |
| `name_embedding` | VECTOR(768) | - | Semantic search vector |

**Industry Constraints:**
- Retail
- Hospitality  
- E-commerce
- Wholesale
- Manufacturing
- Distribution

### 2. Contacts
**Purpose:** Store contact person information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `contact_id` | BIGSERIAL | PRIMARY KEY | Unique contact identifier |
| `first_name` | TEXT | - | Contact first name |
| `last_name` | TEXT | - | Contact last name |
| `contact_email` | TEXT | UNIQUE | Contact email (PK/association key) |
| `mobile_phone` | TEXT | - | Mobile phone (+[countrycode][digits]) |
| `company_domain` | TEXT | FK → companies.company_domain | Associated company |
| `name_embedding` | VECTOR(768) | - | Fuzzy person lookup vector |

### 3. Deals
**Purpose:** Store sales deals and opportunities

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `deal_id` | TEXT | PRIMARY KEY | Deal identifier |
| `deal_name` | TEXT | NOT NULL | Deal name |
| `deal_stage` | TEXT | CHECK constraint | Deal stage |
| `pipeline` | TEXT | - | Sales pipeline |
| `amount` | NUMERIC(18,2) | - | Deal amount |
| `close_date` | TEXT | - | Close date (dd/mm/yyyy hh:mm) |
| `contact_email` | TEXT | FK → contacts.contact_email | Associated contact |
| `company_domain` | TEXT | FK → companies.company_domain | Associated company |
| `product_of_interest` | TEXT | CHECK constraint | Product of interest |
| `point_of_contact` | TEXT | - | Point of contact |
| `description` | TEXT | - | Deal notes or associate emails |
| `name_embedding` | VECTOR(768) | - | Semantic search vector |

**Deal Stage Constraints:**
- Appointment Scheduled
- Qualified to Buy
- Presentation Scheduled
- Closed Won
- Closed Lost

**Product of Interest Constraints:**
- 2-slice toaster
- 4-slice toaster
- smart toaster
- crumb tray kit
- display stand

### 4. Tickets
**Purpose:** Store support tickets and issues

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `ticket_id` | TEXT | PRIMARY KEY | Ticket identifier |
| `ticket_name` | TEXT | NOT NULL | Ticket name |
| `pipeline` | TEXT | DEFAULT 'Support Pipeline' | Support pipeline |
| `ticket_status` | TEXT | CHECK constraint | Ticket status |
| `priority` | TEXT | CHECK constraint | Priority level |
| `source` | TEXT | CHECK constraint | Ticket source |
| `ticket_owner` | TEXT | - | Ticket owner email |
| `activity_date` | TEXT | - | Activity date (dd/mm/yyyy hh:mm) |
| `contact_email` | TEXT | FK → contacts.contact_email | Associated contact |
| `company_domain` | TEXT | FK → companies.company_domain | Associated company |
| `issue_of_interest` | TEXT | CHECK constraint | Issue type |
| `issued_before` | TEXT | CHECK constraint | Previous ticket status |
| `description` | TEXT | - | Ticket notes and/or associated emails |
| `name_embedding` | VECTOR(768) | - | Semantic search vector |
| `issue_embedding` | VECTOR(768) | - | Issue search vector |

**Ticket Status Constraints:**
- New
- Open
- Waiting on contact
- Waiting on Us
- Closed

**Priority Constraints:**
- Low
- Medium
- High

**Source Constraints:**
- Email
- Phone
- Web form

**Issue of Interest Constraints:**
- Crumb tray
- Overheating
- Wi‑Fi setup
- Shipping delay
- Thermostat
- Packaging
- Noise
- Invoice

**Issued Before Constraints:**
- Yes
- No

### 5. Products
**Purpose:** Store product catalog information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `product_id` | BIGSERIAL | PRIMARY KEY | Unique product identifier |
| `name` | TEXT | NOT NULL UNIQUE | Product name |
| `description` | TEXT | - | Product description |
| `price` | NUMERIC(18,2) | - | Product price |
| `cost_of_goods_sold` | NUMERIC(18,2) | - | COGS |
| `description_embedding` | VECTOR(768) | - | Semantic search vector |

### 6. Users
**Purpose:** Store system users and owners

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | BIGSERIAL | PRIMARY KEY | Unique user identifier |
| `email` | TEXT | NOT NULL UNIQUE | User email |
| `full_name` | TEXT | - | User full name |

## Activity Tables

### 7. Tasks
**Purpose:** Task management and assignments

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `task_id` | BIGSERIAL | PRIMARY KEY | Unique task identifier |
| `due_at` | TIMESTAMPTZ | - | Task due date |
| `title` | TEXT | NOT NULL | Task title |
| `notes` | TEXT | - | Task notes |
| `priority` | TEXT | - | Task priority |
| `status` | TEXT | - | Task status |
| `task_type` | TEXT | - | Task type |
| `queue` | TEXT | - | Task queue |
| `assigned_to_user_id` | BIGINT | FK → users.user_id | Assigned user |
| `deal_id` | TEXT | FK → deals.deal_id | Associated deal |
| `title_embedding` | VECTOR(768) | - | Semantic search vector |
| `notes_embedding` | VECTOR(768) | - | Semantic search vector |

### 8. Calls
**Purpose:** Call records and communications

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `call_id` | BIGSERIAL | PRIMARY KEY | Unique call identifier |
| `notes` | TEXT | - | Call notes |
| `direction` | TEXT | - | Inbound/Outbound |
| `status` | TEXT | - | Completed/Busy/etc. |
| `title` | TEXT | - | Call title |
| `activity_at` | TIMESTAMPTZ | - | Call timestamp |
| `assigned_to_user_id` | BIGINT | FK → users.user_id | Assigned user |
| `duration_ms` | BIGINT | - | Call duration |
| `outcome` | TEXT | - | Connected/Left voicemail/etc. |
| `source` | TEXT | - | VoIP/Zoom/etc. |
| `from_number` | TEXT | - | Caller number |
| `to_number` | TEXT | - | Recipient number |
| `recording_url` | TEXT | - | Recording URL |
| `transcript_available` | BOOLEAN | - | Transcript availability |
| `call_meeting_type` | TEXT | - | Meeting type |
| `notes_embedding` | VECTOR(768) | - | Conversational context search |

### 9. Emails
**Purpose:** Email communications

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `email_id` | BIGSERIAL | PRIMARY KEY | Unique email identifier |
| `contact_email` | TEXT | FK → contacts.contact_email | Associated contact |
| `subject` | TEXT | - | Email subject |
| `send_status` | TEXT | - | Sent/Scheduled/etc. |
| `body` | TEXT | - | Email body |
| `direction` | TEXT | - | Incoming/Outgoing |
| `subject_embedding` | VECTOR(768) | - | Semantic search vector |
| `body_embedding` | VECTOR(768) | - | Semantic search vector |

### 10. Notes
**Purpose:** General notes and documentation

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `note_id` | BIGSERIAL | PRIMARY KEY | Unique note identifier |
| `body` | TEXT | NOT NULL | Note content |
| `activity_date` | DATE | - | Activity date |
| `activity_assigned_to_user_id` | BIGINT | FK → users.user_id | Assigned user |
| `company_domain` | TEXT | FK → companies.company_domain | Associated company |
| `ticket_id` | TEXT | FK → tickets.ticket_id | Associated ticket |
| `deal_id` | TEXT | FK → deals.deal_id | Associated deal |
| `contact_email` | TEXT | FK → contacts.contact_email | Associated contact |
| `body_embedding` | VECTOR(768) | - | Long-form context search |

### 11. Deal Line Items
**Purpose:** Line items within deals

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `line_item_id` | BIGSERIAL | PRIMARY KEY | Unique line item identifier |
| `deal_id` | TEXT | FK → deals.deal_id | Associated deal |
| `product_id` | BIGINT | FK → products.product_id | Associated product |
| `name` | TEXT | - | Line item name |
| `quantity` | INTEGER | NOT NULL DEFAULT 1 | Quantity |
| `unit_price` | NUMERIC(18,2) | - | Unit price |

## Association Tables

### 12. Company-Contact Associations
**Purpose:** Many-to-many company-contact relationships

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `company_domain` | TEXT | FK → companies.company_domain | Company domain |
| `contact_email` | TEXT | FK → contacts.contact_email | Contact email |
| `label` | TEXT | DEFAULT '' | Association label |

**Primary Key:** `(company_domain, contact_email, label)`

### 13. Deal-Company Associations
**Purpose:** Many-to-many deal-company relationships

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `deal_id` | TEXT | FK → deals.deal_id | Deal identifier |
| `company_domain` | TEXT | FK → companies.company_domain | Company domain |
| `label` | TEXT | DEFAULT '' | Association label |

**Primary Key:** `(deal_id, company_domain, label)`

### 14. Contact-Contact Associations
**Purpose:** Many-to-many contact-contact relationships

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `contact_email` | TEXT | FK → contacts.contact_email | Contact email |
| `associated_contact_email` | TEXT | FK → contacts.contact_email | Associated contact email |
| `label` | TEXT | DEFAULT '' | Association label |

**Primary Key:** `(contact_email, associated_contact_email, label)`

### 15. Company-Company Associations
**Purpose:** Many-to-many company-company relationships

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `company_domain` | TEXT | FK → companies.company_domain | Company domain |
| `associated_company_domain` | TEXT | FK → companies.company_domain | Associated company domain |
| `label` | TEXT | DEFAULT '' | Association label |

**Primary Key:** `(company_domain, associated_company_domain, label)`

### 16. Call-Contact Associations
**Purpose:** Many-to-many call-contact relationships

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `call_id` | BIGINT | FK → calls.call_id | Call identifier |
| `contact_email` | TEXT | FK → contacts.contact_email | Contact email |

**Primary Key:** `(call_id, contact_email)`

## Key Changes from Previous Schema

### Field Renames
- `contacts.email` → `contacts.contact_email`
- `contacts.phone` → `contacts.mobile_phone`
- `companies.domain` → `companies.company_domain`
- `companies.phone_number` → `companies.phone`
- `deals.name` → `deals.deal_name`
- `deals.stage` → `deals.deal_stage`
- `tickets.name` → `tickets.ticket_name`
- `tickets.status` → `tickets.ticket_status`
- `tickets.owner_user_id` → `tickets.ticket_owner`

### New Fields
- `companies.industry` - Industry classification with constraints
- `companies.number_of_employees` - Employee count
- `deals.description` - Deal notes and associated emails
- `tickets.description` - Ticket notes and associated emails
- `tickets.issued_before` - Whether customer had previous tickets

### Type Changes
- `deals.deal_id` - BIGSERIAL → TEXT
- `tickets.ticket_id` - BIGSERIAL → TEXT
- `deals.close_date` - DATE → TEXT (dd/mm/yyyy hh:mm format)
- `tickets.activity_date` - New TEXT field (dd/mm/yyyy hh:mm format)

### Foreign Key Updates
- All association tables now use `contact_email` and `company_domain` instead of IDs
- This provides better data consistency and easier querying

## Vector Search Support
All text fields that benefit from semantic search have corresponding VECTOR(768) embedding fields for AI-powered search and analysis.

## Data Format Standards
- **Phone Numbers:** +[countrycode][digits] format
- **Dates:** dd/mm/yyyy hh:mm format for deals and tickets
- **Email:** Standard email format for contacts and users
- **Domain:** Standard domain format for companies