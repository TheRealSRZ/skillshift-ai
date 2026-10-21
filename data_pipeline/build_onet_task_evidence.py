"""Attach explicitly reviewed O*NET occupational tasks to SkillShift career skills.

Output is evidence for skill relevance, NOT an official skill importance score.
Never changes careers.json or the existing skill importance evidence.

Run from repo root: python data_pipeline/build_onet_task_evidence.py
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAREERS = ROOT / 'data/careers.json'
MAPPINGS = ROOT / 'data/onet_career_mapping.json'
TASKS = ROOT / 'data/processed/onet_occupation_tasks.csv'
OUT = ROOT / 'data/processed/onet_task_skill_evidence.json'

# Explicit human-reviewed candidate links, NOT automatic matching.
# An empty list means no sufficiently specific task in the provided task CSV.
TASK_LINKS = {
  'role_software_developer': {
    'skill_software_configuration': [21670,21666],
    'skill_software_design': [21662,21667],
    'skill_software_testing': [21669],
    'skill_ai_fluency': [],
    'skill_critical_thinking': [],
    'skill_innovative_thinking': [],
  },
  'role_accountant_auditor': {
    'skill_financial_analysis_reporting': [21514,21532],
    'skill_accounting_principles': [21508,21515],
    'skill_attention_to_detail': [21516,21512],
    'skill_ethical_judgement': [],
    'skill_cost_benefit_analysis': [21519,21531],
    'skill_innovative_thinking': [],
  },
  'role_data_professional': {
    'skill_data_analysis': [21823,21831],
    'skill_data_cleaning': [21826],
    'skill_python': [],
    'skill_sql': [],
    'skill_data_viz': [21828],
    'skill_critical_thinking': [],
  },
  'role_marketing_professional': {
    'skill_marketing_strategy': [5439,5440],
    'skill_digital_marketing': [],
    'skill_market_research': [5433,5443],
    'skill_campaign_performance': [5438],
    'skill_marketing_communication': [5434,5440],
    'skill_critical_thinking': [],
  },
  'role_electrical_engineer': {
    'skill_electrical_system_design': [1348,1364],
    'skill_electrical_circuits': [1348,1358],
    'skill_electrical_safety': [20731,1350],
    'skill_electrical_fault_diagnosis': [1365,20730],
    'skill_electrical_simulation': [1349],
    'skill_critical_thinking': [],
  },
  'role_nursing_professional': {
    'skill_patient_care_monitoring': [1841,1840],
    'skill_nursing_assessment_care_planning': [1843,1842],
    'skill_medication_safety': [20413],
    'skill_infection_prevention': [1860],
    'skill_patient_communication': [1850],
    'skill_critical_thinking': [],
  },
}

# Some task-to-skill relationships are broad/partial; don't overclaim.
PARTIAL = {
 ('role_software_developer','skill_software_configuration'),
 ('role_accountant_auditor','skill_cost_benefit_analysis'),
 ('role_marketing_professional','skill_marketing_strategy'),
 ('role_electrical_engineer','skill_electrical_circuits'),
 ('role_electrical_engineer','skill_electrical_fault_diagnosis'),
 ('role_electrical_engineer','skill_electrical_simulation'),
 ('role_nursing_professional','skill_infection_prevention'),
}

def load_json(path): return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    careers = [x for x in load_json(CAREERS) if x.get('evidence_status') != 'synthetic_demo']
    mapping = {'role_' + x['career_id']: x for x in load_json(MAPPINGS)}
    with TASKS.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    task_index = {}
    for row in rows:
        if row['Scale ID'] != 'IM': continue
        key=(row['O*NET-SOC Code'], str(row['Task ID']))
        if key in task_index: raise ValueError(f'Duplicate task importance row: {key}')
        task_index[key]=row
    if set(TASK_LINKS)!= {c['id'] for c in careers}:
        raise ValueError('Career mapping set differs from current career catalog; review TASK_LINKS')
    result=[]
    for career in careers:
        cid=career['id']; code=mapping[cid]['onet_code']; links=TASK_LINKS[cid]
        if set(links)!=set(career['required_skills']):
            raise ValueError(f'Skill list changed for {cid}; manually review TASK_LINKS')
        for skill,ids in links.items():
            records=[]
            for task_id in ids:
                row=task_index.get((code,str(task_id)))
                if row is None: raise ValueError(f'Missing exact O*NET task {code} / {task_id}')
                if row['Recommend Suppress'].strip().upper()=='Y':
                    raise ValueError(f'Suppressed O*NET task {code} / {task_id}')
                records.append({'task_id':str(task_id),'task_text':row['Task'],
                                'task_importance_1_to_5':float(row['Data Value']),
                                'rating_date':row.get('Date_rating') or row['Date'],
                                'task_type':row['Task Type']})
            etype='none_in_available_tasks' if not records else ('partial_task_relevance' if (cid,skill) in PARTIAL else 'task_relevance')
            result.append({'career_id':cid,'masco_code':career['masco_code'],'onet_code':code,
                           'skill_id':skill,'current_team_weight':career['required_skills'][skill],
                           'evidence_type':etype,'tasks':records,
                           'proposed_weight_1_to_4':None,
                           'note':('Explicitly reviewed O*NET task references; task IM measures importance of the OCCUPATIONAL TASK, not importance of this SkillShift skill. No score conversion.' if records else 'No sufficiently specific O*NET task IM reference in the supplied extract; retain existing team estimate; check other sources.')})
    output={'dataset_id':'onet_task_skill_evidence_v1','source':'O*NET task ratings, supplied data/processed/onet_occupation_tasks.csv',
            'method':'Explicit manual task-ID crosswalk, validated against the occupation-specific IM rows; no keyword scoring or mean-task-score conversion',
            'limitations':['US occupational task evidence is not measured Malaysian skill importance or employer demand.',
                          'A related task is evidence of relevance, not an official skill rating.',
                          'Task links and partial mappings are team-reviewed interpretations and should be peer-reviewed.',
                          'Nursing task examples do not establish Malaysian registration or scope of practice.',
                          'These data do not modify careers.json or backend match scores.'],
            'career_skill_evidence':result}
    OUT.parent.mkdir(exist_ok=True,parents=True)
    OUT.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"PASS: {len(result)} career-skill entries -> {OUT}")
    print(f"Task-linked: {sum(bool(x['tasks']) for x in result)}; no exact task match: {sum(not x['tasks'] for x in result)}")
    print('NOTE: No career weights changed. Task importance is NOT an official skill importance score.')

if __name__=='__main__':main()
