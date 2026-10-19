import type { RoadmapResponse } from '../types'
export default function RoadmapPage({roadmap}:{roadmap:RoadmapResponse|null}){
  return <section><h2>Personalized Reskilling Pathway</h2>{roadmap?<><p>{roadmap.note}</p>
    {roadmap.steps.length?<ol>{roadmap.steps.map(step=><li key={step.course_id}><a href={step.url} target="_blank" rel="noopener noreferrer">{step.title}</a> — {step.estimated_hours??'?'} estimated hours. {step.reason}</li>)}</ol>:<p>No verified courses are available in the starter catalog. Member 4 must validate real resources.</p>}
    <p>Uncovered skills: {roadmap.uncovered_skills.join(', ')||'None'}</p></>:<p>Analyze a profile first; Member 3 integrates the RunPod-supported roadmap next.</p>}
  </section>
}
