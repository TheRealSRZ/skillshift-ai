import type { TrendData } from '../types'
export default function TrendsPage({trend}:{trend:TrendData|null}){
  return <section><h2>Future Skills Radar</h2><p>Starter trend fixture; replace with dated verified Malaysian observations.</p>
    {trend?<><p><strong>{trend.label}</strong></p><p>Snapshot: {trend.snapshot_id} | Date: {trend.observed_date} | Region: {trend.region}</p>
      <ul>{Object.entries(trend.multipliers).map(([id,v])=><li key={id}>{id}: demo multiplier {v}</li>)}</ul></>:<p>Trend data unavailable.</p>}
  </section>
}
