-- ============================================================
-- Supabase schema for Affiliate Products + Click Tracking
-- VERSION 2 — safe to rerun, drops policies before recreating
-- ============================================================

create extension if not exists "pgcrypto";

-- ─────────────────────────────────────────
-- 1. CATEGORIES
-- ─────────────────────────────────────────
create table if not exists public.affiliate_categories (
  id         uuid        primary key default gen_random_uuid(),
  name       text        not null unique,
  created_at timestamptz not null default now()
);

alter table public.affiliate_categories enable row level security;

drop policy if exists "categories_select_public" on public.affiliate_categories;
create policy "categories_select_public"
on public.affiliate_categories
for select
using (true);

-- ─────────────────────────────────────────
-- 2. PRODUCTS
-- ─────────────────────────────────────────
create table if not exists public.affiliate_products (
  id             uuid        primary key default gen_random_uuid(),
  name           text        not null,
  category_id    uuid        references public.affiliate_categories(id) on delete set null,
  category       text,
  image_url      text,
  affiliate_link text        not null,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create index if not exists affiliate_products_category_id_idx
  on public.affiliate_products(category_id);

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_affiliate_products_updated_at
  on public.affiliate_products;

create trigger trg_affiliate_products_updated_at
before update on public.affiliate_products
for each row execute function public.set_updated_at();

alter table public.affiliate_products enable row level security;

drop policy if exists "products_select_public" on public.affiliate_products;
create policy "products_select_public"
on public.affiliate_products
for select
using (true);

-- ─────────────────────────────────────────
-- 3. CLICK TRACKING
-- ─────────────────────────────────────────
create table if not exists public.affiliate_clicks (
  id            uuid        primary key default gen_random_uuid(),
  product_id    uuid        not null references public.affiliate_products(id) on delete cascade,
  affiliate_url text,
  user_agent    text,
  ip            inet,
  country_code  text,
  country_name  text,
  user_id       uuid,
  referrer      text,
  utm_source    text,
  utm_medium    text,
  utm_campaign  text,
  utm_term      text,
  utm_content   text,
  created_at    timestamptz not null default now()
);

-- ─────────────────────────────────────────
-- 4. SAFE COLUMN MIGRATION
-- ─────────────────────────────────────────
alter table public.affiliate_clicks
  add column if not exists country_code text,
  add column if not exists country_name text;

-- ─────────────────────────────────────────
-- 5. INDEXES
-- ─────────────────────────────────────────
create index if not exists affiliate_clicks_product_id_created_at_idx
  on public.affiliate_clicks(product_id, created_at desc);

create index if not exists affiliate_clicks_country_code_created_at_idx
  on public.affiliate_clicks(country_code, created_at desc);

-- ─────────────────────────────────────────
-- 6. RLS ON CLICKS
-- ─────────────────────────────────────────
alter table public.affiliate_clicks enable row level security;

drop policy if exists "clicks_insert_authenticated" on public.affiliate_clicks;
create policy "clicks_insert_authenticated"
on public.affiliate_clicks
for insert
to authenticated
with check (true);

drop policy if exists "clicks_insert_anon" on public.affiliate_clicks;
create policy "clicks_insert_anon"
on public.affiliate_clicks
for insert
to anon
with check (true);

-- ─────────────────────────────────────────
-- 7. VERIFY
-- ─────────────────────────────────────────
select column_name, data_type
from information_schema.columns
where table_schema = 'public'
  and table_name   = 'affiliate_clicks'
order by ordinal_position;