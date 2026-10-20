import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Skill, TrendData } from '../types'

export default function TrendsPage({ trend, skills }: { trend: TrendData | null; skills: Skill[] }) {
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id

  const data = trend
    ? Object.entries(trend.multipliers)
        .map(([id, value]) => ({ name: nameOf(id), value }))
        .sort((a, b) => b.value - a.value)
    : []

  return (
    <section>
      <h2>Future Skills Radar</h2>
      <p>Starter trend fixture; replace with dated verified Malaysian observations.</p>
      {trend ? (
        <>
          <p><strong>{trend.label}</strong></p>
          <p>Snapshot: {trend.snapshot_id} | Date: {trend.observed_date} | Region: {trend.region}</p>
          <div style={{ width: '100%', height: Math.max(220, data.length * 50) }}>
            <ResponsiveContainer>
              <BarChart data={data} layout="vertical" margin={{ left: 20, right: 40 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 'auto']} />
                <YAxis type="category" dataKey="name" width={160} />
                <Tooltip />
                <Bar dataKey="value" name="Demo multiplier" fill="#167b8a">
                  <LabelList dataKey="value" position="right" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <small>Demo values, not real market data.</small>
        </>
      ) : (
        <p>Trend data unavailable.</p>
      )}
    </section>
  )
}