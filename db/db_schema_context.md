# HubSpot CRM Database Schema

## Core Tables

### users
- user_id bigint NOT NULL DEFAULT nextval('users_user_id_seq'::regclass)
- email text NOT NULL
- full_name text NULL
- **PK:** user_id
- **Unique:** email

### companies
- company_id bigint NOT NULL DEFAULT nextval('companies_company_id_seq'::regclass)
- name text NOT NULL
- domain text NULL
- phone_number text NULL
- city text NULL
- name_embedding USER-DEFINED NULL
- **PK:** company_id
- **Unique:** domain

### contacts
- contact_id bigint NOT NULL DEFAULT nextval('contacts_contact_id_seq'::regclass)
- external_id bigint NULL
- first_name text NULL
- last_name text NULL
- email text NULL
- phone text NULL
- name_embedding USER-DEFINED NULL
- **PK:** contact_id
- **Unique:** external_id, email

### products
- product_id bigint NOT NULL DEFAULT nextval('products_product_id_seq'::regclass)
- external_id bigint NULL
- name text NOT NULL
- description text NULL
- price numeric NULL
- cost_of_goods_sold numeric NULL
- description_embedding USER-DEFINED NULL
- **PK:** product_id
- **Unique:** external_id, name

### deals
- deal_id bigint NOT NULL DEFAULT nextval('deals_deal_id_seq'::regclass)
- external_id bigint NULL
- name text NOT NULL
- pipeline text NULL
- stage text NULL
- amount numeric NULL
- close_date date NULL
- product_of_interest text NULL
- point_of_contact_name text NULL
- name_embedding USER-DEFINED NULL
- **PK:** deal_id
- **Unique:** external_id

### tickets
- ticket_id bigint NOT NULL DEFAULT nextval('tickets_ticket_id_seq'::regclass)
- name text NOT NULL
- pipeline text NULL
- status text NULL
- priority text NULL
- owner_user_id bigint NULL
- source text NULL
- issue_of_interest text NULL
- issued_ticket_before boolean NULL
- name_embedding USER-DEFINED NULL
- issue_embedding USER-DEFINED NULL
- **PK:** ticket_id
- **FK:** owner_user_id -> users.user_id

### tasks
- task_id bigint NOT NULL DEFAULT nextval('tasks_task_id_seq'::regclass)
- due_at timestamp with time zone NULL
- title text NOT NULL
- notes text NULL
- priority text NULL
- status text NULL
- task_type text NULL
- queue text NULL
- assigned_to_user_id bigint NULL
- deal_id bigint NULL
- title_embedding USER-DEFINED NULL
- notes_embedding USER-DEFINED NULL
- **PK:** task_id
- **FK:** assigned_to_user_id -> users.user_id, deal_id -> deals.deal_id

### calls
- call_id bigint NOT NULL DEFAULT nextval('calls_call_id_seq'::regclass)
- notes text NULL
- direction text NULL
- status text NULL
- title text NULL
- activity_at timestamp with time zone NULL
- assigned_to_user_id bigint NULL
- duration_ms bigint NULL
- outcome text NULL
- source text NULL
- from_number text NULL
- to_number text NULL
- recording_url text NULL
- transcript_available boolean NULL
- call_meeting_type text NULL
- notes_embedding USER-DEFINED NULL
- **PK:** call_id
- **FK:** assigned_to_user_id -> users.user_id

### emails
- email_id bigint NOT NULL DEFAULT nextval('emails_email_id_seq'::regclass)
- contact_id bigint NULL
- subject text NULL
- send_status text NULL
- body text NULL
- direction text NULL
- subject_embedding USER-DEFINED NULL
- body_embedding USER-DEFINED NULL
- **PK:** email_id
- **FK:** contact_id -> contacts.contact_id

### notes
- note_id bigint NOT NULL DEFAULT nextval('notes_note_id_seq'::regclass)
- body text NOT NULL
- activity_date date NULL
- activity_assigned_to_user_id bigint NULL
- company_id bigint NULL
- ticket_id bigint NULL
- deal_id bigint NULL
- contact_id bigint NULL
- body_embedding USER-DEFINED NULL
- **PK:** note_id
- **FK:** activity_assigned_to_user_id -> users.user_id, company_id -> companies.company_id, ticket_id -> tickets.ticket_id, deal_id -> deals.deal_id, contact_id -> contacts.contact_id

## Association Tables

### company_contact_associations
- company_id bigint NOT NULL
- contact_id bigint NOT NULL
- label text NOT NULL DEFAULT ''::text
- **PK:** company_id, contact_id, label
- **FK:** company_id -> companies.company_id, contact_id -> contacts.contact_id

### deal_company_associations
- deal_id bigint NOT NULL
- company_id bigint NOT NULL
- label text NOT NULL DEFAULT ''::text
- **PK:** deal_id, company_id, label
- **FK:** deal_id -> deals.deal_id, company_id -> companies.company_id

### contact_contact_associations
- contact_id bigint NOT NULL
- associated_contact_id bigint NOT NULL
- label text NOT NULL DEFAULT ''::text
- **PK:** contact_id, associated_contact_id, label
- **FK:** contact_id -> contacts.contact_id, associated_contact_id -> contacts.contact_id

### company_company_associations
- company_id bigint NOT NULL
- associated_company_id bigint NOT NULL
- label text NOT NULL DEFAULT ''::text
- **PK:** company_id, associated_company_id, label
- **FK:** company_id -> companies.company_id, associated_company_id -> companies.company_id

### call_contacts
- call_id bigint NOT NULL
- contact_id bigint NOT NULL
- **PK:** call_id, contact_id
- **FK:** call_id -> calls.call_id, contact_id -> contacts.contact_id

### deal_line_items
- line_item_id bigint NOT NULL DEFAULT nextval('deal_line_items_line_item_id_seq'::regclass)
- deal_id bigint NOT NULL
- product_id bigint NULL
- name text NULL
- quantity integer NOT NULL DEFAULT 1
- unit_price numeric NULL
- **PK:** line_item_id
- **FK:** deal_id -> deals.deal_id, product_id -> products.product_id

## Table Relationships

- **users** referenced by: tickets.owner_user_id, tasks.assigned_to_user_id, calls.assigned_to_user_id, notes.activity_assigned_to_user_id
- **companies** referenced by: company_contact_associations.company_id, deal_company_associations.company_id, company_company_associations.company_id, notes.company_id
- **contacts** referenced by: company_contact_associations.contact_id, contact_contact_associations.contact_id, call_contacts.contact_id, emails.contact_id, notes.contact_id
- **deals** referenced by: deal_company_associations.deal_id, deal_line_items.deal_id, tasks.deal_id, notes.deal_id
- **products** referenced by: deal_line_items.product_id
- **tickets** referenced by: notes.ticket_id
- **calls** referenced by: call_contacts.call_id