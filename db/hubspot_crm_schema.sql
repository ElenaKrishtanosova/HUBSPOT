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
	domain TEXT UNIQUE,
	phone_number TEXT,
	city TEXT,
	-- semantic search (company naming, fuzzy matching, dedupe)
	name_embedding VECTOR(768)
);

CREATE TABLE contacts (
	contact_id BIGSERIAL PRIMARY KEY,
	external_id BIGINT UNIQUE, -- "Record ID - Contacts" when present
	first_name TEXT,
	last_name TEXT,
	email TEXT UNIQUE,
	phone TEXT,
	-- for fuzzy person lookup (e.g., “Jon Smyth from Dragonfly”)
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

CREATE TABLE deals (
	deal_id BIGSERIAL PRIMARY KEY,
	external_id BIGINT UNIQUE, -- "Deal ID" / "Deal Unique Value (RecordID)"
	name TEXT NOT NULL,
	pipeline TEXT,
	stage TEXT,
	amount NUMERIC(18,2),
	close_date DATE,
	product_of_interest TEXT,
	point_of_contact_name TEXT,
	-- semantic search on how the deal is described/named
	name_embedding VECTOR(768)
);

CREATE TABLE deal_line_items (
	line_item_id BIGSERIAL PRIMARY KEY,
	deal_id BIGINT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
	product_id BIGINT REFERENCES products(product_id),
	name TEXT,
	quantity INTEGER NOT NULL DEFAULT 1,
	unit_price NUMERIC(18,2)
);

CREATE TABLE tickets (
	ticket_id BIGSERIAL PRIMARY KEY,
	name TEXT NOT NULL,
	pipeline TEXT,
	status TEXT,
	priority TEXT,
	owner_user_id BIGINT REFERENCES users(user_id),
	source TEXT,
	issue_of_interest TEXT,
	issued_ticket_before BOOLEAN,
	-- search on summarized issue/title for support workflows
	name_embedding VECTOR(768),
	issue_embedding VECTOR(768)
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
	contact_id BIGINT REFERENCES contacts(contact_id),
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
	company_id BIGINT REFERENCES companies(company_id),
	ticket_id BIGINT REFERENCES tickets(ticket_id),
	deal_id BIGINT REFERENCES deals(deal_id),
	contact_id BIGINT REFERENCES contacts(contact_id),
	-- long-form context used by reps
	body_embedding VECTOR(768)
);

-- Associations (many-to-many, with labels)

CREATE TABLE company_contact_associations (
	company_id BIGINT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
	contact_id BIGINT NOT NULL REFERENCES contacts(contact_id) ON DELETE CASCADE,
	label TEXT DEFAULT '',
	PRIMARY KEY (company_id, contact_id, label)
);

CREATE TABLE deal_company_associations (
	deal_id BIGINT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
	company_id BIGINT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
	label TEXT DEFAULT '',
	PRIMARY KEY (deal_id, company_id, label)
);

CREATE TABLE contact_contact_associations (
	contact_id BIGINT NOT NULL REFERENCES contacts(contact_id) ON DELETE CASCADE,
	associated_contact_id BIGINT NOT NULL REFERENCES contacts(contact_id) ON DELETE CASCADE,
	label TEXT DEFAULT '',
	PRIMARY KEY (contact_id, associated_contact_id, label)
);

CREATE TABLE company_company_associations (
	company_id BIGINT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
	associated_company_id BIGINT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
	label TEXT DEFAULT '',
	PRIMARY KEY (company_id, associated_company_id, label)
);

-- Calls can be linked to one or more contacts (from "Calls and contacts ...")
CREATE TABLE call_contacts (
	call_id BIGINT NOT NULL REFERENCES calls(call_id) ON DELETE CASCADE,
	contact_id BIGINT NOT NULL REFERENCES contacts(contact_id) ON DELETE CASCADE,
	PRIMARY KEY (call_id, contact_id)
);

-- Helpful uniqueness/lookup indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);
CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
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
