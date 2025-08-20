-- Enable pgvector for VECTOR(768) columns used in semantic/ML features
CREATE EXTENSION IF NOT EXISTS vector;

-- Users/Owners (assignees/owners referenced across activities)
CREATE TABLE users (
	user_id BIGSERIAL PRIMARY KEY,
	email TEXT NOT NULL UNIQUE,
	full_name TEXT
);

-- Core CRM objects

CREATE TABLE companies (
	company_id BIGSERIAL PRIMARY KEY,
	name TEXT NOT NULL,
	company_domain TEXT UNIQUE,
	phone TEXT,
	city TEXT,
	industry TEXT CHECK (industry IN ('Retail', 'Hospitality', 'E-commerce', 'Wholesale', 'Manufacturing', 'Distribution')),
	number_of_employees INTEGER,
	-- semantic search (company naming, fuzzy matching, dedupe)
	name_embedding VECTOR(768)
);

CREATE TABLE contacts (
	contact_id BIGSERIAL PRIMARY KEY,
	first_name TEXT,
	last_name TEXT,
	contact_email TEXT UNIQUE,
	mobile_phone TEXT,
	company_domain TEXT REFERENCES companies(company_domain),
	-- for fuzzy person lookup (e.g., "Jon Smyth from Dragonfly")
	name_embedding VECTOR(768)
);

CREATE TABLE products (
	product_id BIGSERIAL PRIMARY KEY,
	external_id BIGINT UNIQUE, -- "Product ID (Existing)" from imports
	name TEXT NOT NULL UNIQUE,
	description TEXT,
	price NUMERIC(18,2),
	cost_of_goods_sold NUMERIC(18,2),
	-- semantic search on catalog text
	description_embedding VECTOR(768)
);

-- Deals table
CREATE TABLE deals (
    deal_id BIGSERIAL PRIMARY KEY,
    deal_name TEXT NOT NULL,
    deal_stage TEXT CHECK (deal_stage IN ('Appointment Scheduled', 'Qualified to Buy', 'Presentation Scheduled', 'Closed Won', 'Closed Lost')),
    pipeline TEXT DEFAULT 'Sales Pipeline',
    amount NUMERIC(10,2),
    close_date TEXT CHECK (close_date ~ '^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$'),
    contact_email TEXT REFERENCES contacts(contact_email),
    company_domain TEXT REFERENCES companies(company_domain),
    product_of_interest TEXT CHECK (product_of_interest IN ('2-slice toaster', '4-slice toaster', 'smart toaster', 'crumb tray kit', 'display stand')),
    point_of_contact TEXT,
    description TEXT,
    name_embedding vector(768)
);

CREATE TABLE deal_line_items (
	line_item_id BIGSERIAL PRIMARY KEY,
	deal_id BIGINT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
	product_id BIGINT REFERENCES products(product_id),
	name TEXT,
	quantity INTEGER NOT NULL DEFAULT 1,
	unit_price NUMERIC(18,2)
);

-- Tickets table
CREATE TABLE tickets (
    ticket_id BIGSERIAL PRIMARY KEY,
    ticket_name TEXT NOT NULL,
    pipeline TEXT DEFAULT 'Support Pipeline',
    ticket_status TEXT CHECK (ticket_status IN ('New', 'Open', 'Waiting on contact', 'Waiting on Us', 'Closed')),
    priority TEXT CHECK (priority IN ('Low', 'Medium', 'High')),
    source TEXT CHECK (source IN ('Email', 'Phone', 'Web form')),
    ticket_owner TEXT,
    activity_date TEXT CHECK (activity_date ~ '^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$'),
    contact_email TEXT REFERENCES contacts(contact_email),
    company_domain TEXT REFERENCES companies(company_domain),
    issue_of_interest TEXT CHECK (issue_of_interest IN ('Crumb tray', 'Overheating', 'Wi‑Fi setup', 'Shipping delay', 'Thermostat', 'Packaging', 'Noise', 'Invoice')),
    issued_before TEXT CHECK (issued_before IN ('Yes', 'No')),
    description TEXT,
    name_embedding vector(768),
    issue_embedding vector(768)
);

-- Activities

CREATE TABLE tasks (
	task_id BIGSERIAL PRIMARY KEY,
	due_at TIMESTAMPTZ,
	title TEXT NOT NULL,
	notes TEXT,
	priority TEXT,
	status TEXT,
	task_type TEXT,
	queue TEXT,
	assigned_to_user_id BIGINT REFERENCES users(user_id),
	deal_id BIGINT REFERENCES deals(deal_id),
	-- task intent and content search
	title_embedding VECTOR(768),
	notes_embedding VECTOR(768)
);

CREATE TABLE calls (
	call_id BIGSERIAL PRIMARY KEY,
	notes TEXT,
	direction TEXT,             -- Inbound/Outbound
	status TEXT,                -- Completed/Busy/etc.
	title TEXT,
	activity_at TIMESTAMPTZ,
	assigned_to_user_id BIGINT REFERENCES users(user_id),
	duration_ms BIGINT,
	outcome TEXT,               -- Connected/Left voicemail/etc.
	source TEXT,                -- VoIP/Zoom/etc.
	from_number TEXT,
	to_number TEXT,
	recording_url TEXT,
	transcript_available BOOLEAN,
	call_meeting_type TEXT,
	-- conversational context search
	notes_embedding VECTOR(768)
);

CREATE TABLE emails (
	email_id BIGSERIAL PRIMARY KEY,
	contact_email TEXT REFERENCES contacts(contact_email),
	subject TEXT,
	send_status TEXT,           -- Sent/Scheduled/etc.
	body TEXT,
	direction TEXT,             -- Incoming/Outgoing
	-- search on intent and content
	subject_embedding VECTOR(768),
	body_embedding VECTOR(768)
);

CREATE TABLE notes (
	note_id BIGSERIAL PRIMARY KEY,
	body TEXT NOT NULL,
	activity_date DATE,
	activity_assigned_to_user_id BIGINT REFERENCES users(user_id),
	company_domain TEXT REFERENCES companies(company_domain),
	ticket_id BIGINT REFERENCES tickets(ticket_id),
	deal_id BIGINT REFERENCES deals(deal_id),
	contact_email TEXT REFERENCES contacts(contact_email),
	-- long-form context used by reps
	body_embedding VECTOR(768)
);

-- Associations (many-to-many, with labels)

CREATE TABLE company_contact_associations (
	company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
	contact_email TEXT NOT NULL REFERENCES contacts(contact_email) ON DELETE CASCADE,
	label TEXT DEFAULT '',
	PRIMARY KEY (company_domain, contact_email, label)
);

CREATE TABLE deal_company_associations (
	deal_id BIGINT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
	company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
	label TEXT DEFAULT '',
	PRIMARY KEY (deal_id, company_domain, label)
);

CREATE TABLE contact_contact_associations (
	contact_email TEXT NOT NULL REFERENCES contacts(contact_email) ON DELETE CASCADE,
	associated_contact_email TEXT NOT NULL REFERENCES contacts(contact_email) ON DELETE CASCADE,
	label TEXT DEFAULT '',
	PRIMARY KEY (contact_email, associated_contact_email, label)
);

CREATE TABLE company_company_associations (
	company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
	associated_company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
	label TEXT DEFAULT '',
	PRIMARY KEY (company_domain, associated_company_domain, label)
);

-- Calls can be linked to one or more contacts (from "Calls and contacts ...")
CREATE TABLE call_contacts (
	call_id BIGINT NOT NULL REFERENCES calls(call_id) ON DELETE CASCADE,
	contact_email TEXT NOT NULL REFERENCES contacts(contact_email),
	PRIMARY KEY (call_id, contact_email)
);

-- Helpful uniqueness/lookup indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_domain ON companies(company_domain);
CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_email ON contacts(contact_email);
CREATE UNIQUE INDEX IF NOT EXISTS idx_products_name ON products(name);

-- ANN indexes for vector search (tune lists based on data size)
-- Use cosine similarity by default; switch ops class if using dot_product or l2
CREATE INDEX IF NOT EXISTS idx_companies_name_vec ON companies USING ivfflat (name_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_contacts_name_vec ON contacts USING ivfflat (name_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_products_desc_vec ON products USING ivfflat (description_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_deals_name_vec ON deals USING ivfflat (name_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_tickets_name_vec ON tickets USING ivfflat (name_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_tickets_issue_vec ON tickets USING ivfflat (issue_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_tasks_title_vec ON tasks USING ivfflat (title_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_tasks_notes_vec ON tasks USING ivfflat (notes_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_calls_notes_vec ON calls USING ivfflat (notes_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_emails_subject_vec ON emails USING ivfflat (subject_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_emails_body_vec ON emails USING ivfflat (body_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_notes_body_vec ON notes USING ivfflat (body_embedding vector_cosine_ops) WITH (lists = 100);
