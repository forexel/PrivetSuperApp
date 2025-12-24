--
-- PostgreSQL database dump
--

\restrict lRPbwZwV2lvxVX2GI73qznEZjbTjEsxmTHdVrPoVPodW8RmUTfG0clNHUiXPFWA

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 16.10 (Debian 16.10-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: changed_by_t; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.changed_by_t AS ENUM (
    'system',
    'user',
    'operator',
    'master',
    'USER'
);


ALTER TYPE public.changed_by_t OWNER TO privet;

--
-- Name: invoice_status_t; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.invoice_status_t AS ENUM (
    'pending',
    'paid',
    'canceled'
);


ALTER TYPE public.invoice_status_t OWNER TO privet;

--
-- Name: manager_client_status_t; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.manager_client_status_t AS ENUM (
    'new',
    'in_verification',
    'awaiting_contract',
    'awaiting_payment',
    'processed'
);


ALTER TYPE public.manager_client_status_t OWNER TO privet;

--
-- Name: messageauthor; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.messageauthor AS ENUM (
    'user',
    'support'
);


ALTER TYPE public.messageauthor OWNER TO privet;

--
-- Name: support_sender_t; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.support_sender_t AS ENUM (
    'manager',
    'client',
    'system'
);


ALTER TYPE public.support_sender_t OWNER TO privet;

--
-- Name: supportcasestatus; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.supportcasestatus AS ENUM (
    'open',
    'pending',
    'resolved',
    'closed'
);


ALTER TYPE public.supportcasestatus OWNER TO privet;

--
-- Name: tariff_period_t; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.tariff_period_t AS ENUM (
    'month',
    'year'
);


ALTER TYPE public.tariff_period_t OWNER TO privet;

--
-- Name: tariff_plan_t; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.tariff_plan_t AS ENUM (
    'simple',
    'medium',
    'premium'
);


ALTER TYPE public.tariff_plan_t OWNER TO privet;

--
-- Name: ticket_status_t; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.ticket_status_t AS ENUM (
    'accepted',
    'in_progress',
    'done',
    'rejected',
    'new'
);


ALTER TYPE public.ticket_status_t OWNER TO privet;

--
-- Name: ticketstatus; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.ticketstatus AS ENUM (
    'open',
    'pending',
    'closed'
);


ALTER TYPE public.ticketstatus OWNER TO privet;

--
-- Name: user_status_t; Type: TYPE; Schema: public; Owner: privet
--

CREATE TYPE public.user_status_t AS ENUM (
    'ghost',
    'active',
    'blocked',
    'deleted'
);


ALTER TYPE public.user_status_t OWNER TO privet;

--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: privet
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_updated_at() OWNER TO privet;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.alembic_version (
    version_num character varying(64) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO privet;

--
-- Name: device_photos; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.device_photos (
    id uuid NOT NULL,
    device_id uuid NOT NULL,
    file_url character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.device_photos OWNER TO privet;

--
-- Name: devices; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.devices (
    id uuid NOT NULL,
    user_id uuid,
    title character varying NOT NULL,
    brand character varying NOT NULL,
    model character varying NOT NULL,
    serial_number character varying NOT NULL,
    purchase_date date,
    warranty_until date,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.devices OWNER TO privet;

--
-- Name: faq_articles; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.faq_articles (
    id uuid NOT NULL,
    category_id uuid NOT NULL,
    title character varying NOT NULL,
    content text NOT NULL,
    keywords character varying[] NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.faq_articles OWNER TO privet;

--
-- Name: faq_categories; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.faq_categories (
    id uuid NOT NULL,
    slug character varying NOT NULL,
    title character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.faq_categories OWNER TO privet;

--
-- Name: manager_clients; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.manager_clients (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    assigned_manager_id uuid,
    status public.manager_client_status_t DEFAULT 'new'::public.manager_client_status_t NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    support_ticket_id uuid
);


ALTER TABLE public.manager_clients OWNER TO privet;

--
-- Name: manager_support_messages; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.manager_support_messages (
    id uuid NOT NULL,
    thread_id uuid NOT NULL,
    sender public.support_sender_t NOT NULL,
    content text NOT NULL,
    payload json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.manager_support_messages OWNER TO privet;

--
-- Name: manager_support_threads; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.manager_support_threads (
    id uuid NOT NULL,
    client_id uuid NOT NULL,
    title character varying(256) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.manager_support_threads OWNER TO privet;

--
-- Name: manager_tariffs; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.manager_tariffs (
    id uuid NOT NULL,
    name character varying(128) NOT NULL,
    base_fee numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    extra_per_device numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.manager_tariffs OWNER TO privet;

--
-- Name: manager_users; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.manager_users (
    id uuid NOT NULL,
    email character varying NOT NULL,
    password_hash text NOT NULL,
    name character varying,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_super_admin boolean DEFAULT false NOT NULL
);


ALTER TABLE public.manager_users OWNER TO privet;

--
-- Name: master_users; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.master_users (
    id uuid NOT NULL,
    email character varying,
    phone character varying NOT NULL,
    password_hash character varying NOT NULL,
    name character varying NOT NULL,
    status public.user_status_t DEFAULT 'active'::public.user_status_t NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    has_subscription boolean NOT NULL,
    address text
);


ALTER TABLE public.master_users OWNER TO privet;

--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.password_reset_tokens (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    token character varying NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.password_reset_tokens OWNER TO privet;

--
-- Name: sessions; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    refresh_token character varying NOT NULL,
    user_agent character varying,
    ip character varying,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sessions OWNER TO privet;

--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.subscriptions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    plan public.tariff_plan_t NOT NULL,
    period public.tariff_period_t NOT NULL,
    active boolean DEFAULT true NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    paid_until timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.subscriptions OWNER TO privet;

--
-- Name: support_messages; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.support_messages (
    id uuid NOT NULL,
    ticket_id uuid NOT NULL,
    author public.messageauthor NOT NULL,
    body text NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.support_messages OWNER TO privet;

--
-- Name: support_tickets; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.support_tickets (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    subject character varying(255) NOT NULL,
    status public.supportcasestatus DEFAULT 'open'::public.supportcasestatus NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.support_tickets OWNER TO privet;

--
-- Name: ticket_attachments; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.ticket_attachments (
    id uuid NOT NULL,
    ticket_id uuid NOT NULL,
    file_url text NOT NULL,
    file_type text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ticket_attachments OWNER TO privet;

--
-- Name: ticket_status_history; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.ticket_status_history (
    id uuid NOT NULL,
    ticket_id uuid NOT NULL,
    from_status public.ticket_status_t,
    to_status public.ticket_status_t NOT NULL,
    changed_by public.changed_by_t NOT NULL,
    comment text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ticket_status_history OWNER TO privet;

--
-- Name: tickets; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.tickets (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    device_id uuid,
    title character varying(255) NOT NULL,
    description text,
    preferred_date date,
    status public.ticket_status_t DEFAULT 'new'::public.ticket_status_t NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    closed_at timestamp with time zone
);


ALTER TABLE public.tickets OWNER TO privet;

--
-- Name: user_contracts; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.user_contracts (
    id uuid NOT NULL,
    client_id uuid NOT NULL,
    tariff_snapshot json NOT NULL,
    passport_snapshot json NOT NULL,
    device_snapshot json NOT NULL,
    otp_code character varying(16),
    otp_sent_at timestamp with time zone,
    signed_at timestamp with time zone,
    payment_confirmed_at timestamp with time zone,
    contract_url character varying(512),
    contract_number character varying(64),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    pep_agreed_at timestamp with time zone,
    signature_hash character varying(64),
    signature_hmac character varying(128),
    signed_ip character varying(64),
    signed_user_agent character varying(512)
);


ALTER TABLE public.user_contracts OWNER TO privet;

--
-- Name: user_device_photos; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.user_device_photos (
    id uuid NOT NULL,
    device_id uuid NOT NULL,
    file_key character varying(512) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone
);


ALTER TABLE public.user_device_photos OWNER TO privet;

--
-- Name: user_devices; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.user_devices (
    id uuid NOT NULL,
    client_id uuid NOT NULL,
    device_type character varying(64) NOT NULL,
    title character varying(128) NOT NULL,
    description text,
    specs json,
    extra_fee numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_devices OWNER TO privet;

--
-- Name: user_invoice_payments; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.user_invoice_payments (
    id uuid NOT NULL,
    invoice_id uuid NOT NULL,
    client_id uuid NOT NULL,
    amount integer NOT NULL,
    status character varying(32) DEFAULT 'success'::character varying NOT NULL,
    paid_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_invoice_payments OWNER TO privet;

--
-- Name: user_invoices; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.user_invoices (
    id uuid NOT NULL,
    client_id uuid NOT NULL,
    amount numeric(10,2) NOT NULL,
    description text NOT NULL,
    contract_number character varying(64) NOT NULL,
    due_date date NOT NULL,
    status public.invoice_status_t DEFAULT 'pending'::public.invoice_status_t NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_invoices OWNER TO privet;

--
-- Name: user_tariffs; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.user_tariffs (
    id uuid NOT NULL,
    client_id uuid NOT NULL,
    tariff_id uuid,
    device_count integer DEFAULT 0 NOT NULL,
    total_extra_fee numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    calculated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_tariffs OWNER TO privet;

--
-- Name: users; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying,
    phone character varying NOT NULL,
    password_hash character varying NOT NULL,
    name character varying NOT NULL,
    status public.user_status_t DEFAULT 'active'::public.user_status_t NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    has_subscription boolean NOT NULL,
    address text
);


ALTER TABLE public.users OWNER TO privet;

--
-- Name: users_passports; Type: TABLE; Schema: public; Owner: privet
--

CREATE TABLE public.users_passports (
    id uuid NOT NULL,
    client_id uuid NOT NULL,
    last_name character varying(128),
    first_name character varying(128),
    middle_name character varying(128),
    series character varying(16),
    number character varying(16),
    issued_by character varying(256),
    issue_code character varying(16),
    issue_date date,
    registration_address character varying(512),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    photo_url character varying(512)
);


ALTER TABLE public.users_passports OWNER TO privet;

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: device_photos device_photos_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.device_photos
    ADD CONSTRAINT device_photos_pkey PRIMARY KEY (id);


--
-- Name: devices devices_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (id);


--
-- Name: devices devices_serial_number_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_serial_number_key UNIQUE (serial_number);


--
-- Name: faq_articles faq_articles_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.faq_articles
    ADD CONSTRAINT faq_articles_pkey PRIMARY KEY (id);


--
-- Name: faq_categories faq_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.faq_categories
    ADD CONSTRAINT faq_categories_pkey PRIMARY KEY (id);


--
-- Name: faq_categories faq_categories_slug_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.faq_categories
    ADD CONSTRAINT faq_categories_slug_key UNIQUE (slug);


--
-- Name: manager_clients manager_clients_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_clients
    ADD CONSTRAINT manager_clients_pkey PRIMARY KEY (id);


--
-- Name: manager_support_messages manager_support_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_support_messages
    ADD CONSTRAINT manager_support_messages_pkey PRIMARY KEY (id);


--
-- Name: manager_support_threads manager_support_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_support_threads
    ADD CONSTRAINT manager_support_threads_pkey PRIMARY KEY (id);


--
-- Name: manager_tariffs manager_tariffs_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_tariffs
    ADD CONSTRAINT manager_tariffs_pkey PRIMARY KEY (id);


--
-- Name: manager_users manager_users_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_users
    ADD CONSTRAINT manager_users_pkey PRIMARY KEY (id);


--
-- Name: master_users master_users_phone_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.master_users
    ADD CONSTRAINT master_users_phone_key UNIQUE (phone);


--
-- Name: master_users master_users_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.master_users
    ADD CONSTRAINT master_users_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_token_key UNIQUE (token);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_refresh_token_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_refresh_token_key UNIQUE (refresh_token);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: support_messages support_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.support_messages
    ADD CONSTRAINT support_messages_pkey PRIMARY KEY (id);


--
-- Name: support_tickets support_tickets_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.support_tickets
    ADD CONSTRAINT support_tickets_pkey PRIMARY KEY (id);


--
-- Name: ticket_attachments ticket_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.ticket_attachments
    ADD CONSTRAINT ticket_attachments_pkey PRIMARY KEY (id);


--
-- Name: ticket_status_history ticket_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.ticket_status_history
    ADD CONSTRAINT ticket_status_history_pkey PRIMARY KEY (id);


--
-- Name: tickets tickets_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_pkey PRIMARY KEY (id);


--
-- Name: manager_users uq_manager_users_email; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_users
    ADD CONSTRAINT uq_manager_users_email UNIQUE (email);


--
-- Name: user_contracts user_contracts_client_id_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_contracts
    ADD CONSTRAINT user_contracts_client_id_key UNIQUE (client_id);


--
-- Name: user_contracts user_contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_contracts
    ADD CONSTRAINT user_contracts_pkey PRIMARY KEY (id);


--
-- Name: user_device_photos user_device_photos_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_device_photos
    ADD CONSTRAINT user_device_photos_pkey PRIMARY KEY (id);


--
-- Name: user_devices user_devices_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_devices
    ADD CONSTRAINT user_devices_pkey PRIMARY KEY (id);


--
-- Name: user_invoice_payments user_invoice_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_invoice_payments
    ADD CONSTRAINT user_invoice_payments_pkey PRIMARY KEY (id);


--
-- Name: user_invoices user_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_invoices
    ADD CONSTRAINT user_invoices_pkey PRIMARY KEY (id);


--
-- Name: user_tariffs user_tariffs_client_id_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_tariffs
    ADD CONSTRAINT user_tariffs_client_id_key UNIQUE (client_id);


--
-- Name: user_tariffs user_tariffs_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_tariffs
    ADD CONSTRAINT user_tariffs_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users_passports users_passports_client_id_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.users_passports
    ADD CONSTRAINT users_passports_client_id_key UNIQUE (client_id);


--
-- Name: users_passports users_passports_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.users_passports
    ADD CONSTRAINT users_passports_pkey PRIMARY KEY (id);


--
-- Name: users users_phone_key; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_phone_key UNIQUE (phone);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_password_reset_tokens_user_id; Type: INDEX; Schema: public; Owner: privet
--

CREATE INDEX ix_password_reset_tokens_user_id ON public.password_reset_tokens USING btree (user_id);


--
-- Name: ix_sessions_user_id; Type: INDEX; Schema: public; Owner: privet
--

CREATE INDEX ix_sessions_user_id ON public.sessions USING btree (user_id);


--
-- Name: ix_support_messages_ticket_id; Type: INDEX; Schema: public; Owner: privet
--

CREATE INDEX ix_support_messages_ticket_id ON public.support_messages USING btree (ticket_id);


--
-- Name: ix_support_tickets_user_id; Type: INDEX; Schema: public; Owner: privet
--

CREATE INDEX ix_support_tickets_user_id ON public.support_tickets USING btree (user_id);


--
-- Name: ix_user_invoice_payments_client_id; Type: INDEX; Schema: public; Owner: privet
--

CREATE INDEX ix_user_invoice_payments_client_id ON public.user_invoice_payments USING btree (client_id);


--
-- Name: ix_user_invoice_payments_invoice_id; Type: INDEX; Schema: public; Owner: privet
--

CREATE INDEX ix_user_invoice_payments_invoice_id ON public.user_invoice_payments USING btree (invoice_id);


--
-- Name: uq_manager_clients_user; Type: INDEX; Schema: public; Owner: privet
--

CREATE UNIQUE INDEX uq_manager_clients_user ON public.manager_clients USING btree (user_id);


--
-- Name: user_device_photos trg_user_device_photos_updated_at; Type: TRIGGER; Schema: public; Owner: privet
--

CREATE TRIGGER trg_user_device_photos_updated_at BEFORE UPDATE ON public.user_device_photos FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: user_tariffs trg_user_tariffs_updated_at; Type: TRIGGER; Schema: public; Owner: privet
--

CREATE TRIGGER trg_user_tariffs_updated_at BEFORE UPDATE ON public.user_tariffs FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: device_photos device_photos_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.device_photos
    ADD CONSTRAINT device_photos_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id);


--
-- Name: devices devices_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: faq_articles faq_articles_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.faq_articles
    ADD CONSTRAINT faq_articles_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.faq_categories(id);


--
-- Name: manager_clients fk_manager_clients_support_ticket; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_clients
    ADD CONSTRAINT fk_manager_clients_support_ticket FOREIGN KEY (support_ticket_id) REFERENCES public.support_tickets(id) ON DELETE SET NULL;


--
-- Name: manager_clients manager_clients_assigned_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_clients
    ADD CONSTRAINT manager_clients_assigned_manager_id_fkey FOREIGN KEY (assigned_manager_id) REFERENCES public.manager_users(id) ON DELETE SET NULL;


--
-- Name: manager_clients manager_clients_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_clients
    ADD CONSTRAINT manager_clients_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: manager_support_messages manager_support_messages_thread_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_support_messages
    ADD CONSTRAINT manager_support_messages_thread_id_fkey FOREIGN KEY (thread_id) REFERENCES public.manager_support_threads(id) ON DELETE CASCADE;


--
-- Name: manager_support_threads manager_support_threads_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.manager_support_threads
    ADD CONSTRAINT manager_support_threads_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.manager_clients(id) ON DELETE CASCADE;


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: subscriptions subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: support_messages support_messages_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.support_messages
    ADD CONSTRAINT support_messages_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.support_tickets(id) ON DELETE CASCADE;


--
-- Name: ticket_attachments ticket_attachments_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.ticket_attachments
    ADD CONSTRAINT ticket_attachments_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.tickets(id) ON DELETE CASCADE;


--
-- Name: ticket_status_history ticket_status_history_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.ticket_status_history
    ADD CONSTRAINT ticket_status_history_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.tickets(id) ON DELETE CASCADE;


--
-- Name: tickets tickets_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id);


--
-- Name: tickets tickets_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_contracts user_contracts_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_contracts
    ADD CONSTRAINT user_contracts_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.manager_clients(id) ON DELETE CASCADE;


--
-- Name: user_device_photos user_device_photos_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_device_photos
    ADD CONSTRAINT user_device_photos_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.user_devices(id) ON DELETE CASCADE;


--
-- Name: user_devices user_devices_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_devices
    ADD CONSTRAINT user_devices_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.manager_clients(id) ON DELETE CASCADE;


--
-- Name: user_invoice_payments user_invoice_payments_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_invoice_payments
    ADD CONSTRAINT user_invoice_payments_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_invoice_payments user_invoice_payments_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_invoice_payments
    ADD CONSTRAINT user_invoice_payments_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.user_invoices(id) ON DELETE CASCADE;


--
-- Name: user_invoices user_invoices_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_invoices
    ADD CONSTRAINT user_invoices_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_tariffs user_tariffs_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_tariffs
    ADD CONSTRAINT user_tariffs_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.manager_clients(id) ON DELETE CASCADE;


--
-- Name: user_tariffs user_tariffs_tariff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.user_tariffs
    ADD CONSTRAINT user_tariffs_tariff_id_fkey FOREIGN KEY (tariff_id) REFERENCES public.manager_tariffs(id) ON DELETE SET NULL;


--
-- Name: users_passports users_passports_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: privet
--

ALTER TABLE ONLY public.users_passports
    ADD CONSTRAINT users_passports_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.manager_clients(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict lRPbwZwV2lvxVX2GI73qznEZjbTjEsxmTHdVrPoVPodW8RmUTfG0clNHUiXPFWA

