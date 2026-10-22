import type { AnalyzeResponse, Career, Profile, RoadmapResponse, Skill, TrendData, MarketSignalsResponse } from '../types'

export class ApiError extends Error {
  constructor(public readonly status: number, message: string, public readonly retryAfter: number | null = null) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch('/api' + path, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!response.ok) {
    let message = `Request failed (HTTP ${response.status}).`
    try {
      const body: unknown = await response.json()
      if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') {
        message = body.detail
      }
    } catch { /* Don't expose upstream implementation details. */ }
    const retryAfterHeader = response.headers.get('Retry-After')
    const retryAfter = retryAfterHeader && /^\d+$/.test(retryAfterHeader) ? Number(retryAfterHeader) : null
    throw new ApiError(response.status, message, retryAfter)
  }
  return await response.json() as T
}
export const api = {
  catalog: () => request<{ skills: Skill[]; careers: Career[] }>('/catalog'),
  trends: () => request<TrendData>('/trends'),
  marketSignals: () => request<MarketSignalsResponse>('/market-signals', {cache: 'no-store'}),
  analyze: (profile: Profile, scenario: string) => request<AnalyzeResponse>('/analyze', { method:'POST',body:JSON.stringify({ profile, scenario }) }),
  scenarios: (profile: Profile) => request<{ moderate: AnalyzeResponse; rapid: AnalyzeResponse }>('/scenarios', {method:'POST',body:JSON.stringify({ profile, scenario:'moderate' })}),
  roadmap: (role: string, missing: string[], scenario: string) => request<RoadmapResponse>('/roadmap', {method:'POST',body:JSON.stringify({ target_role:role, missing_skills:missing, scenario })}),
  personalizeRoadmap: (role: string, missing: string[], scenario: string, accessToken: string) => request<RoadmapResponse>('/roadmap/personalize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${accessToken}` },
    body: JSON.stringify({ target_role: role, missing_skills: missing, scenario }),
  }),
  sdgs: () => request<{mappings: {sdg:number; title:string; rationale:string}[];note:string}>('/sdgs'),
}
