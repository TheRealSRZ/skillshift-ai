import type { AnalyzeResponse, Profile, RoadmapResponse } from '../types'
import { supabase } from './supabase'

export type StoredProfile = {
  user_id: string
  display_name: string
  education: string
  skills: string[]
  interests: string[]
  target_role: string
  theme: 'light' | 'dark'
}
export type AnalysisRecord = {
  id: string
  target_role: string
  scenario: string
  saved_at: string
}
export type RoadmapRecord = {
  id: string
  target_role: string
  scenario: string
  saved_at: string
}
function client() {
  if (!supabase) throw new Error('Supabase is not configured')
  return supabase
}
export async function loadProfile(userId: string): Promise<StoredProfile | null> {
  const { data, error } = await client().from('profiles').select(
    'user_id,display_name,education,skills,interests,target_role,theme'
  ).eq('user_id', userId).maybeSingle()
  if (error) throw error
  return data as StoredProfile | null
}
export async function saveProfile(
  userId: string, displayName: string, profile: Profile, roleId: string, theme: 'light' | 'dark'
): Promise<void> {
  const record: StoredProfile = {
    user_id: userId, display_name: displayName.trim().slice(0, 100),
    education: profile.education.slice(0, 160),
    skills: [...new Set(profile.skills)].slice(0, 30),
    interests: [...new Set(profile.interests)].slice(0, 12),
    target_role: roleId.slice(0, 100), theme,
  }
  const { error } = await client().from('profiles').upsert(record, { onConflict: 'user_id' })
  if (error) throw error
}
export async function saveAnalysis(
  userId: string, profile: Profile, roleId: string, result: AnalyzeResponse
): Promise<void> {
  const { error } = await client().from('saved_analyses').insert({
    user_id: userId, target_role: roleId,
    scenario: result.scenario, profile_snapshot: profile, result,
  })
  if (error) throw error
}
export async function saveRoadmap(userId: string, roadmap: RoadmapResponse): Promise<void> {
  const { error } = await client().from('saved_roadmaps').insert({
    user_id: userId, target_role: roadmap.target_role,
    scenario: roadmap.scenario, roadmap,
  })
  if (error) throw error
}
export async function listAnalyses(userId: string): Promise<AnalysisRecord[]> {
  const { data, error } = await client().from('saved_analyses')
    .select('id,target_role,scenario,saved_at').eq('user_id', userId)
    .order('saved_at', { ascending: false }).limit(10)
  if (error) throw error
  return data as AnalysisRecord[]
}
export async function listRoadmaps(userId: string): Promise<RoadmapRecord[]> {
  const { data, error } = await client().from('saved_roadmaps')
    .select('id,target_role,scenario,saved_at').eq('user_id', userId)
    .order('saved_at', { ascending: false }).limit(10)
  if (error) throw error
  return data as RoadmapRecord[]
}
export async function deleteAnalysis(userId: string, id: string): Promise<void> {
  const { error } = await client().from('saved_analyses').delete().eq('id', id).eq('user_id', userId)
  if (error) throw error
}
export async function deleteRoadmap(userId: string, id: string): Promise<void> {
  const { error } = await client().from('saved_roadmaps').delete().eq('id', id).eq('user_id', userId)
  if (error) throw error
}
