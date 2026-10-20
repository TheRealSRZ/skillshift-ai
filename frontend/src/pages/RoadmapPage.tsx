import type { Career, RoadmapResponse, Skill } from '../types'

export default function RoadmapPage({ roadmap, skills, careers }: { roadmap: RoadmapResponse | null; skills: Skill[]; careers: Career[] }) {
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id
  const cleanText = (text: string) => text.replace(/skill_[a-z0-9_]+/g, id => nameOf(id))
  const roleTitle = careers.find(c => c.id === roadmap?.target_role)?.title ?? roadmap?.target_role

  const totalHours = roadmap
    ? Math.round(roadmap.steps.reduce((sum, s) => sum + (s.estimated_hours ?? 0), 0) * 100) / 100
    : 0

  return (
    <section>
      <h2>Personalized Reskilling Pathway</h2>
      {roadmap ? (
        <>
          <p>{roadmap.note}</p>
          {roadmap.steps.length ? (
            <>
              <p>
                Pathway for: <strong>{roleTitle}</strong> | Total estimated time: <strong>{totalHours} hours</strong>
              </p>
              <ol>
                {roadmap.steps.map(step => (
                  <li key={step.course_id}>
                    <strong>Step {step.step}:</strong>{' '}
                    <a href={step.url} target="_blank" rel="noopener noreferrer">{step.title}</a>
                    {' '}— {step.estimated_hours ?? '?'} estimated hours. {cleanText(step.reason)}
                  </li>
                ))}
              </ol>
            </>
          ) : (
            <p>No verified courses are available in the starter catalog. Member 4 must validate real resources.</p>
          )}
          <p>
            Uncovered skills: {roadmap.uncovered_skills.map(nameOf).join(', ') || 'None'}
          </p>
        </>
      ) : (
        <p>Analyze a profile first; Member 3 integrates the RunPod-supported roadmap next.</p>
      )}
    </section>
  )
}