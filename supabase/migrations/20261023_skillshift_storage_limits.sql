-- SkillShift AI | Additive storage abuse controls for existing Supabase tables.
-- Apply after 20261020_skillshift_accounts.sql in the SAME Supabase project.
-- Does not remove or rewrite saved user data. Existing oversized records are
-- not retroactively validated; future inserts must satisfy these constraints.
-- No extra service, extension, or background worker is required.

-- Each account's stored objects have bounded serialized sizes. jsonb::text is
-- a reasonable approximation of stored payload size (not actual disk usage).
ALTER TABLE public.saved_analyses
  ADD CONSTRAINT analyses_profile_size_limit
    CHECK (octet_length(profile_snapshot::text) <= 32768) NOT VALID;
ALTER TABLE public.saved_analyses
  ADD CONSTRAINT analyses_result_size_limit
    CHECK (octet_length(result::text) <= 131072) NOT VALID;
ALTER TABLE public.saved_analyses
  ADD CONSTRAINT analyses_target_role_size_limit
    CHECK (char_length(target_role) <= 100) NOT VALID;
ALTER TABLE public.saved_roadmaps
  ADD CONSTRAINT roadmaps_result_size_limit
    CHECK (octet_length(roadmap::text) <= 131072) NOT VALID;
ALTER TABLE public.saved_roadmaps
  ADD CONSTRAINT roadmaps_target_role_size_limit
    CHECK (char_length(target_role) <= 100) NOT VALID;

-- Existing per-array count checks remain. Enforce byte budgets on client-written
-- arrays too; React-side .slice() is not an authorization boundary.
ALTER TABLE public.profiles
  ADD CONSTRAINT profile_skills_bytes_limit
    CHECK (octet_length(array_to_string(skills, ',')) <= 4000
           AND array_position(skills, NULL) IS NULL) NOT VALID;
ALTER TABLE public.profiles
  ADD CONSTRAINT profile_interests_bytes_limit
    CHECK (octet_length(array_to_string(interests, ',')) <= 2400
           AND array_position(interests, NULL) IS NULL) NOT VALID;

-- Private trigger functions: not exposed as publicly callable Data API RPCs.
CREATE SCHEMA IF NOT EXISTS skillshift_internal;
REVOKE ALL ON SCHEMA skillshift_internal FROM PUBLIC, anon, authenticated;

-- Advisory transaction locks serialize concurrent inserts for the same account
-- so concurrent requests can't both pass the COUNT() check.
CREATE OR REPLACE FUNCTION skillshift_internal.guard_saved_analyses()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  -- Check identity *before* counting to avoid cross-account record-count oracles.
  IF NEW.user_id IS DISTINCT FROM (SELECT auth.uid()) THEN
    RAISE EXCEPTION 'Not authorized to save results' USING ERRCODE = '42501';
  END IF;
  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(NEW.user_id::text || ':analyses', 0));
  IF (SELECT COUNT(*) FROM public.saved_analyses WHERE user_id = NEW.user_id) >= 30 THEN
    RAISE EXCEPTION 'Saved analyses limit reached (30 per account)'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION skillshift_internal.guard_saved_analyses() FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE FUNCTION skillshift_internal.guard_saved_roadmaps()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  -- Check identity *before* counting to avoid cross-account record-count oracles.
  IF NEW.user_id IS DISTINCT FROM (SELECT auth.uid()) THEN
    RAISE EXCEPTION 'Not authorized to save results' USING ERRCODE = '42501';
  END IF;
  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(NEW.user_id::text || ':roadmaps', 0));
  IF (SELECT COUNT(*) FROM public.saved_roadmaps WHERE user_id = NEW.user_id) >= 30 THEN
    RAISE EXCEPTION 'Saved roadmaps limit reached (30 per account)'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION skillshift_internal.guard_saved_roadmaps() FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS limit_saved_analyses_per_user ON public.saved_analyses;
CREATE TRIGGER limit_saved_analyses_per_user
  BEFORE INSERT ON public.saved_analyses FOR EACH ROW
  EXECUTE FUNCTION skillshift_internal.guard_saved_analyses();

DROP TRIGGER IF EXISTS limit_saved_roadmaps_per_user ON public.saved_roadmaps;
CREATE TRIGGER limit_saved_roadmaps_per_user
  BEFORE INSERT ON public.saved_roadmaps FOR EACH ROW
  EXECUTE FUNCTION skillshift_internal.guard_saved_roadmaps();
