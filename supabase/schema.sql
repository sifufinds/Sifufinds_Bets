-- SifuFinds — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query → Run
-- Project: https://supabase.com/dashboard/project/kedfcmgqjxwzebhoeosi

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. LIVE EVENTS  (upserted every 5 min by agent_live_odds.py)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists live_events (
  event_key    text        primary key,        -- home:away:sport_key
  league       text        not null,
  sport_key    text        not null,
  live         boolean     default false,
  complete     boolean     default false,
  home         text,
  away         text,
  h_score      text,
  a_score      text,
  time_disp    text,
  h_odds       numeric(6,2) default 0,
  d_odds       numeric(6,2) default 0,
  a_odds       numeric(6,2) default 0,
  h_bk         text        default '',
  d_bk         text        default '',
  a_bk         text        default '',
  refreshed_at timestamptz not null default now()
);

alter table live_events enable row level security;

create policy "anon_select_live_events"
  on live_events for select
  to anon
  using (true);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. TIPS  (seeded manually; agents can update status after matches)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists tips (
  id          uuid        primary key default gen_random_uuid(),
  created_at  timestamptz default now(),
  league      text,
  sport_key   text,
  match       text,
  pred        text,
  analysis    text,
  odds        text,
  via         text,
  conf        integer,
  time_disp   text,
  date_label  text,
  is_ai       boolean     default false,
  status      text        default 'active',   -- active | won | lost | void
  sort_order  integer     default 0
);

alter table tips enable row level security;

create policy "anon_select_tips"
  on tips for select
  to anon
  using (status = 'active');

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. NEWS ITEMS  (shown on tips page)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists news_items (
  id          uuid        primary key default gen_random_uuid(),
  created_at  timestamptz default now(),
  cat         text,
  color       text,
  title       text,
  date_label  text,
  sort_order  integer     default 0
);

alter table news_items enable row level security;

create policy "anon_select_news"
  on news_items for select
  to anon
  using (true);

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. AGENT LOGS  (operational history, replaces agent_log.json)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists agent_logs (
  id          uuid        primary key default gen_random_uuid(),
  logged_at   timestamptz default now(),
  agent       text        not null,
  action      text,
  status      text,       -- running | success | failed | partial
  detail      text,
  meta        jsonb
);

alter table agent_logs enable row level security;

create policy "anon_select_agent_logs"
  on agent_logs for select
  to anon
  using (true);

-- Auto-prune: keep last 2000 entries (optional — run manually or via cron)
-- delete from agent_logs where id in (
--   select id from agent_logs order by logged_at asc limit (select greatest(count(*)-2000,0) from agent_logs)
-- );

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. AGENT STATE  (replaces scraper_state.json, offers_state.json, etc.)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists agent_state (
  key         text        primary key,   -- 'scraper_state', 'offers_state', etc.
  value       jsonb       not null default '{}',
  updated_at  timestamptz default now()
);

alter table agent_state enable row level security;

create policy "anon_select_agent_state"
  on agent_state for select
  to anon
  using (true);
