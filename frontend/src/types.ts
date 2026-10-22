export type Skill = { id: string; name: string }
export type Career = { id: string; title: string; required_skills: Record<string, number>; sdgs: number[] }
export type Profile = { education: string; skills: string[]; interests: string[] }
export type Match = { role_id: string; title: string; readiness_score: number; matched_skills: string[]; missing_skills: string[]; sdgs: number[] }
export type AnalyzeResponse = { scenario: string; trend_snapshot_id: string; data_label: string; scenario_disclaimer: string; matches: Match[] }
export type TrendData = { snapshot_id: string; label: string; observed_date: string; retrieved_date: string; region: string; multipliers: Record<string, number> }
export type RoadmapStep = { step: number; course_id: string; title: string; url: string; estimated_hours?: number; reason: string }
export type RoadmapResponse = { target_role: string; scenario: string; generation_mode: string; steps: RoadmapStep[]; uncovered_skills: string[]; note: string }
export type Scenario = "moderate" | "rapid";

// Member 4 DOSM comparison evidence. Read-only and separate from synthetic scenario multipliers.
export type MarketSignalBase = {
  career_id: string; career_title: string; masco_code: string
  previous_period: string; latest_period: string; availability_note: string; note: string
  source_urls: string[]; can_directly_adjust_career_scores: false; ai_impact_measure: false
}
export type MarketSignal = MarketSignalBase & (
  | { data_status: 'observed_comparison_available'; previous_job_offerings: number; latest_job_offerings: number; absolute_change: number; percent_change: number; direction: 'increase' | 'decrease' | 'unchanged' }
  | { data_status: 'insufficient_data'; previous_job_offerings: null; latest_job_offerings: null; absolute_change: null; percent_change: null; direction: null }
)
export type MarketSignalsResponse = {
  snapshot_id: string; generated_date: string; geography: string; periods: string[]
  observed_count: number; insufficient_data_count: number
  method: string; limitations: string[]; can_directly_adjust_career_scores: false
  career_signals: MarketSignal[]
}
