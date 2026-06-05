-- SifuFinds — Contact Submissions Table
-- Run this in: Supabase Dashboard → SQL Editor → New Query → Run
-- Project: https://supabase.com/dashboard/project/kedfcmgqjxwzebhoeosi

-- ─────────────────────────────────────────────────────────────────────────────
-- CONTACT SUBMISSIONS  (written by the /contact/ form on the website)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists contact_submissions (
  id             uuid        primary key default gen_random_uuid(),
  created_at     timestamptz default now(),
  full_name      text        not null,
  company_name   text,
  email          text        not null,
  website        text,
  inquiry_type   text        not null,
  budget         text,
  message        text        not null,
  terms_accepted boolean     not null default true,
  status         text        not null default 'new'   -- new | read | replied | archived
);

-- Index for quick lookups by status and date
create index if not exists contact_submissions_status_idx
  on contact_submissions (status, created_at desc);

create index if not exists contact_submissions_email_idx
  on contact_submissions (email);

-- Row Level Security
alter table contact_submissions enable row level security;

-- Anonymous users can insert (submit the form) but NOT read submissions
create policy "anon_insert_contact_submissions"
  on contact_submissions for insert
  to anon
  with check (true);

-- Only authenticated users (e.g. the admin) can read submissions
create policy "auth_select_contact_submissions"
  on contact_submissions for select
  to authenticated
  using (true);

-- Only authenticated users can update status
create policy "auth_update_contact_submissions"
  on contact_submissions for update
  to authenticated
  using (true)
  with check (true);

-- Enable Realtime so the Supabase dashboard reflects new submissions live
-- (Run this separately if needed)
-- alter publication supabase_realtime add table contact_submissions;
