import type { AnalyzeResponse, Career, Profile, RoadmapResponse, Skill, TrendData } from '../types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch('/api' + path, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`)
  return await response.json() as T
}
export const api = {
  catalog: () => request<{ skills: Skill[]; careers: Career[] }>('/catalog'),
  trends: () => request<TrendData>('/trends'),
  analyze: (profile: Profile, scenario: string) => request<AnalyzeResponse>('/analyze', { method:'POST',body:JSON.stringify({ profile, scenario }) }),
  scenarios: (profile: Profile) => request<{ moderate: AnalyzeResponse; rapid: AnalyzeResponse }>('/scenarios', {method:'POST',body:JSON.stringify({ profile, scenario:'moderate' })}),
  roadmap: (role: string, missing: string[], scenario: string) => request<RoadmapResponse>('/roadmap', {method:'POST',body:JSON.stringify({ target_role:role, missing_skills:missing, scenario })}),
  sdgs: () => request<{mappings: {sdg:number; title:string; rationale:string}[];note:string}>('/sdgs'),
}
