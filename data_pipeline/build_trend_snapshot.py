"""Build a proposed, explicitly modelled WEF skill-trend snapshot. Does not overwrite data/trends.json."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'

def read(p): return json.loads(p.read_text(encoding='utf-8'))

def main():
    evidence=read(DATA/'wef_skill_trend_observations.json')
    careers=read(DATA/'careers.json')
    skills=read(DATA/'skills.json')
    sources=read(DATA/'sources.json')
    skillids={s['id'] for s in skills}
    source=next((s for s in sources if s['id']==evidence['source_id']),None)
    assert source is not None, 'WEF source missing from sources.json'
    claimids={c['claim_id'] for c in source['supported_claims']}
    mapped={}
    for item in evidence['mappings']:
        assert item['claim_id'] in claimids, item
        assert item['skill_id'] in skillids, item
        assert item['mapping_provenance']=='team_semantic_mapping', item
        assert item['observed_direction']=='employers_expect_increasing_importance', item
        sid=item['skill_id']
        assert sid not in mapped, f'duplicate {sid}'
        mapped[sid]=item
    # This model policy is team authored. 1.05 DOES NOT represent a 5% measured skills increase.
    factor=evidence['model_policy']['uplift_factor']
    assert type(factor) in (int,float) and 1.0 <= factor <= 1.2
    monitored=[c for c in careers if c['id'] in evidence['target_career_ids']]
    assert len(monitored)==6
    coverage={c['id']:sorted(set(c['required_skills'])&set(mapped)) for c in monitored}
    assert all(coverage.values()), f'Uncovered careers: {coverage}'
    snapshot={
      'snapshot_id':'wef_foj_2025_global_expectations_team_mapping_v1',
      'label':'WEF 2025 global employer skill expectations — TEAM-MAPPED MODEL SIGNAL (not Malaysian observed demand)',
      'observed_date':evidence['published_date'],
      'retrieved_date':evidence['retrieved_date'],
      'region':'global_employer_survey_not_malaysia_specific',
      'source_ids':[evidence['source_id']],
      'evidence_status':'source_reported_direction_team_assigned_numeric_multipliers',
      'multipliers':{sid:factor for sid in sorted(mapped)},
      'signal_provenance':{
        'source_observation':'employer_survey_expected_skill_direction_not_realized_market_change',
        'skill_mapping':'team_semantic_mapping_not_wef_individual_skill_ids',
        'multiplier':'team_defined_illustrative_uplift_not_measured_growth',
        'uplift_factor':factor,
        'policy_version':evidence['model_policy']['version'],
        'source_published_date':evidence['published_date'],
        'limitations':evidence['limitations']
      },
    }
    out=DATA/'processed'/'wef_trend_snapshot_proposed.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: matched 6/6 careers; skill mappings:',', '.join(sorted(mapped)))
    print('PASS: all source/claim/skill IDs resolve; uplift is clearly team-assigned')
    print('Wrote proposed snapshot:',out)
    for cid,sids in coverage.items(): print(' ',cid,':',', '.join(sids))
    print('NOTE: Does NOT replace data/trends.json')

if __name__=='__main__':main()
