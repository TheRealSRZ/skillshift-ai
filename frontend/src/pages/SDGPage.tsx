export default function SDGPage({mappings}:{mappings:{sdg:number;title:string;rationale:string}[]}){
  return <section><h2>SDG Impact</h2><p>Primary target: SDG 4 Quality Education. Contributions shown are proposed, not measured impacts.</p>
    <div className="grid">{mappings.map(s=><article className="card" key={s.sdg}><h3>SDG {s.sdg} — {s.title}</h3><p>{s.rationale}</p></article>)}</div>
  </section>
}
