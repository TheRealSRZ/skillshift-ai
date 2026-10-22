"""Read-only checks and sample outputs for SkillShift AI's proposed Priority 3 models.
Run from repository root: python data_pipeline/validate_priority3_integration.py
Does NOT alter backend or active trends.json. Writes a demo artifact under data/processed/.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def ensure(ok, msg):
    if not ok: raise AssertionError(msg)

def score(role, selected, trend, scenario):
    values={sid: weight*trend.get(sid,1.0)*scenario.get(sid,1.0) for sid,weight in role['required_skills'].items()}
    return round(100*sum(v for k,v in values.items() if k in selected)/sum(values.values()),1)

def main():
    careers=load(DATA/'careers.json'); skills=load(DATA/'skills.json'); sources=load(DATA/'sources.json')
    assumptions=load(DATA/'scenario_assumptions.json')
    snapshot=load(DATA/'processed/wef_trend_snapshot_proposed.json')
    observations=load(DATA/'wef_skill_trend_observations.json')
    uncertainty=load(DATA/'career_ai_uncertainty.json')
    active_trend=load(DATA/'trends.json')
    by_id={r['id']:r for r in careers}; skill_ids={s['id'] for s in skills}; source_ids={s['id'] for s in sources}
    targets={c['career_id'] for c in uncertainty['careers']}
    ensure(len(targets)==6 and len(uncertainty['careers'])==6,'Expected six unique uncertainty careers')
    ensure(targets <= by_id.keys(),'Unknown uncertainty career')
    ensure(set(snapshot['multipliers'])<=skill_ids,'Snapshot references unknown skill')
    ensure(set(snapshot['source_ids'])<=source_ids,'Unknown snapshot source')
    ensure(observations['source_id'] in source_ids,'Unknown observation source')
    ensure(snapshot['signal_provenance']['multiplier'].startswith('team_defined'),'Trend modelling provenance absent')
    ensure('not_malaysia' in snapshot['region'],'Trend geography needs explicit global-only label')
    ensure(all(isinstance(v,(int,float)) and not isinstance(v,bool) and v>0 for v in snapshot['multipliers'].values()),'Invalid trend factors')
    ensure(assumptions['base_scenario']=='moderate' and assumptions['comparison_scenario']=='rapid','Unexpected scenario names')
    factors={}
    for a in assumptions['assumptions']:
        sid=a['skill_id']; ensure(sid in skill_ids,'Unknown scenario skill '+sid)
        ensure(sid not in factors,'Duplicate scenario factor '+sid)
        ensure(a['rapid_multiplier']>0 and a['moderate_multiplier']==1,'Invalid factors')
        ensure(set(a['context_source_ids'])<=source_ids,'Unknown context sources')
        for cid in a['affected_career_ids']:
            ensure(cid in by_id and sid in by_id[cid]['required_skills'],f'Invalid career-skill scenario mapping {cid}/{sid}')
        ensure(a['numeric_multiplier_provenance'],'Missing numeric provenance')
        factors[sid]=a['rapid_multiplier']
    ensure(targets <= {cid for a in assumptions['assumptions'] for cid in a['affected_career_ids']},'Not all six careers included')
    ensure(targets <= {cid for cid in targets if set(by_id[cid]['required_skills']) & set(snapshot['multipliers'])},'Trend not mapped to all six careers')
    ensure(active_trend['snapshot_id']!=snapshot['snapshot_id'],'Proposed snapshot accidentally same as active')
    examples=[]
    for cid in sorted(targets):
        role=by_id[cid]
        scenario_skill=next(a['skill_id'] for a in assumptions['assumptions'] if cid in a['affected_career_ids'])
        trend_skill=next(sid for sid in snapshot['multipliers'] if sid in role['required_skills'])
        neutral=score(role,{scenario_skill},{},{})
        rapid=score(role,{scenario_skill},{},factors)
        trend_base=score(role,{trend_skill},{},{})
        trend_new=score(role,{trend_skill},snapshot['multipliers'],{})
        ensure(rapid!=neutral,f'Scenario does not affect partial user for {cid}')
        ensure(trend_new!=trend_base,f'Trend does not affect partial user for {cid}')
        ensure(score(role,set(),snapshot['multipliers'],factors)==0 and score(role,set(role['required_skills']),snapshot['multipliers'],factors)==100,'Boundary scores broken')
        examples.append({'career_id':cid,'title':role['title'],
          'scenario_test_skill_id':scenario_skill,'moderate_neutral_score':neutral,'rapid_neutral_score':rapid,
          'trend_test_skill_id':trend_skill,'neutral_trend_score':trend_base,'proposed_trend_score':trend_new})
    result={'validation_status':'passed_proposal_only_not_live_api',
      'scenario_version':assumptions['version'],'trend_snapshot_id':snapshot['snapshot_id'],
      'source_observation_type':'WEF global employer expectations; not Malaysian observed skill demand',
      'numeric_factor_type':'team-assigned illustrative sensitivity; not source-measured growth',
      'tested_career_count':6,'sample_profiles':'single-skill hypothetical partial profiles; isolated factor comparisons',
      'examples':examples,'backend_integration':'not tested; Member 2 must verify actual API and scenario route',
      'warning':'A score measures weighted coverage of selected skills, not job placement or loss probability.'}
    path=DATA/'processed/ai_scenarios_trends_validation_results.json'
    path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('PASS: 6/6 target careers have valid scenario and trend mappings')
    print('PASS: source, skill and career references resolve')
    print('PASS: hypothetical scenario and proposed trend each change a controlled partial-profile score in all six careers')
    print('PASS: 0% and 100% boundary cases stay unchanged')
    print('PASS: active trends.json was only read, never modified')
    print('Wrote:',path)
    for x in examples: print(x['career_id'], 'scenario',x['moderate_neutral_score'],'->',x['rapid_neutral_score'],'trend',x['neutral_trend_score'],'->',x['proposed_trend_score'])

if __name__=='__main__': main()
