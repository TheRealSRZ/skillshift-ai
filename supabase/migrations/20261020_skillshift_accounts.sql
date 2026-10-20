-- SkillShift AI Phase 5E | Run once in Supabase SQL Editor.
-- Authentication identities/passwords are managed ONLY by auth.users.
create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default '',
  education text not null default '',
  skills text[] not null default '{}',
  interests text[] not null default '{}',
  target_role text not null default '',
  theme text not null default 'light' check (theme in ('light', 'dark')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint profile_name_length check (char_length(display_name) <= 100),
  constraint profile_education_length check (char_length(education) <= 160),
  constraint profile_skill_count check (cardinality(skills) <= 30),
  constraint profile_interest_count check (cardinality(interests) <= 12),
  constraint profile_role_length check (char_length(target_role) <= 100)
);

create table if not exists public.saved_analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  target_role text not null default '',
  scenario text not null check (scenario in ('moderate', 'rapid')),
  profile_snapshot jsonb not null,
  result jsonb not null,
  saved_at timestamptz not null default now(),
  constraint analyses_profile_object check (jsonb_typeof(profile_snapshot) = 'object'),
  constraint analyses_result_object check (jsonb_typeof(result) = 'object')
);

create table if not exists public.saved_roadmaps (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  target_role text not null,
  scenario text not null check (scenario in ('moderate', 'rapid')),
  roadmap jsonb not null,
  saved_at timestamptz not null default now(),
  constraint roadmaps_result_object check (jsonb_typeof(roadmap) = 'object')
);

create index if not exists saved_analyses_user_time_idx
  on public.saved_analyses(user_id, saved_at desc);
create index if not exists saved_roadmaps_user_time_idx
  on public.saved_roadmaps(user_id, saved_at desc);

alter table public.profiles enable row level security;
alter table public.saved_analyses enable row level security;
alter table public.saved_roadmaps enable row level security;

-- Explicit privilege grants plus user ownership policies. No anon grants.
revoke all on public.profiles from anon;
revoke all on public.saved_analyses from anon;
revoke all on public.saved_roadmaps from anon;
grant select, insert, update, delete on public.profiles to authenticated;
grant select, insert, delete on public.saved_analyses to authenticated;
grant select, insert, delete on public.saved_roadmaps to authenticated;

drop policy if exists profiles_select_own on public.profiles;
create policy profiles_select_own on public.profiles
 for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists profiles_insert_own on public.profiles;
create policy profiles_insert_own on public.profiles
 for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own on public.profiles
 for update to authenticated using ((select auth.uid()) = user_id)
 with check ((select auth.uid()) = user_id);
drop policy if exists profiles_delete_own on public.profiles;
create policy profiles_delete_own on public.profiles
 for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists analyses_select_own on public.saved_analyses;
create policy analyses_select_own on public.saved_analyses
 for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists analyses_insert_own on public.saved_analyses;
create policy analyses_insert_own on public.saved_analyses
 for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists analyses_delete_own on public.saved_analyses;
create policy analyses_delete_own on public.saved_analyses
 for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists roadmaps_select_own on public.saved_roadmaps;
create policy roadmaps_select_own on public.saved_roadmaps
 for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists roadmaps_insert_own on public.saved_roadmaps;
create policy roadmaps_insert_own on public.saved_roadmaps
 for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists roadmaps_delete_own on public.saved_roadmaps;
create policy roadmaps_delete_own on public.saved_roadmaps
 for delete to authenticated using ((select auth.uid()) = user_id);
