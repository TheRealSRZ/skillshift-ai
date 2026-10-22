"""Build a source-separated six-career AI evidence file. No score blending.

Repo placement: data_pipeline/build_career_ai_exposure.py
Required inputs:
 data/careers.json
 data/processed/oecd_ai_exposure_evidence.json
 data/external/ilo/4digits_with_tasks.xlsx
Output: data/processed/career_ai_exposure_six_careers.json

All ILO occupational exposure labels come directly from the ILO explorer workbook.
Task numerical scores are not used as published occupation mean/SD values.
"""
import json
import re
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CAREERS = ROOT / 'data/careers.json'
OECD = ROOT / 'data/processed/oecd_ai_exposure_evidence.json'
ILO = ROOT / 'data/external/ilo/4digits_with_tasks.xlsx'
OUT = ROOT / 'data/processed/career_ai_exposure_six_careers.json'
NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

CODES = {
 'role_software_developer':('2512','direct_comparable'),
 'role_accountant_auditor':('2411','partial_comparable_accountants_only'),
 'role_marketing_professional':('2431','direct_comparable'),
 'role_electrical_engineer':('2151','direct_comparable'),
 'role_nursing_professional':('2221','direct_comparable'),
}


def sheet_rows(path):
    """Read first worksheet (7 columns) without a spreadsheet dependency."""
    with ZipFile(path) as z:
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        relroot = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        rels = {x.get('Id'):x.get('Target') for x in relroot}
        first = wb.find('x:sheets/x:sheet',NS)
        rid = first.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target = rels[rid].lstrip('/')
        path_in_zip = target if target.startswith('xl/') else 'xl/'+target
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall('x:si',NS):
                strings.append(''.join((t.text or '') for t in si.findall('.//x:t',NS)))
        sheet=ET.fromstring(z.read(path_in_zip))
        for row in sheet.findall('x:sheetData/x:row',NS):
            vals=[None]*7
            for cell in row.findall('x:c',NS):
                ref=cell.get('r','')
                m=re.match('[A-Z]+',ref)
                if not m:continue
                pos=0
                for letter in m.group(0):pos=pos*26+ord(letter)-64
                pos-=1
                if pos>=len(vals):continue
                v=cell.find('x:v',NS)
                inline=cell.find('x:is',NS)
                if inline is not None:
                    val=''.join(t.text or '' for t in inline.findall('.//x:t',NS))
                elif v is None or v.text is None:val=None
                elif cell.get('t')=='s':val=strings[int(v.text)]
                else:val=v.text
                vals[pos]=val
            yield vals


def read_ilo(path):
    rows=iter(sheet_rows(path))
    header=next(rows)
    needed=['isco08_4d','isco08_5d','potential25']
    if not all(k in header for k in needed):
        raise ValueError(f'Unexpected ILO workbook header {header}')
    indices=[header.index(k) for k in needed]
    grouped=defaultdict(lambda:{'titles':set(),'categories':set(),'task_count':0})
    for row in rows:
        occupation, task, category=[row[i] for i in indices]
        if not isinstance(occupation,str):continue
        m=re.match(r'^([0-9]{4})\s+-\s+(.+)',occupation)
        if not m:continue
        code,title=m.groups(); entry=grouped[code]
        entry['titles'].add(title); entry['categories'].add(category)
        if isinstance(task,str) and task.strip():entry['task_count']+=1
    output={}
    for code,v in grouped.items():
        if len(v['titles'])!=1 or len(v['categories'])!=1:
            raise ValueError(f'Inconsistent ILO category/title for {code}')
        output[code]={'isco_code':code,'occupation_title':next(iter(v['titles'])),
                      'exposure_category_2025':next(iter(v['categories'])),
                      'task_count':v['task_count']}
    return output


def build():
    careers={c['id']:c for c in json.loads(CAREERS.read_text(encoding='utf-8'))}
    oecd_raw=json.loads(OECD.read_text(encoding='utf-8'))
    oecd={x['career_id']:x for x in oecd_raw['careers']}
    ilo=read_ilo(ILO)
    wanted=list(CODES)+['role_data_professional']
    if len(wanted)!=6 or len(set(wanted))!=6:raise ValueError('Six career IDs required')
    results=[]
    for career_id in wanted:
        if career_id not in careers or career_id not in oecd:
            raise ValueError(f'Missing career or OECD record: {career_id}')
        c=careers[career_id]
        x=oecd[career_id]
        matched=x['oecd_record_status']=='matched_exact_onet_code'
        if matched and (x['baseline_ai_exposure_index_0_to_1'] is None or x['oecd_plus_one_cognitive_scenario_index_0_to_1'] is None):
            raise ValueError(f'Incomplete OECD match: {career_id}')
        if career_id=='role_data_professional':
            ilo_primary={'status':'no_direct_isco_equivalent','isco_code':None,'occupation_title':None,
                         'exposure_category_2025':None,'occupation_mean_score_2025':None,
                         'mapping_quality':'unresolved'}
            reps=[]
            for code,rationale in [('2120','Partial analytical/statistical tasks; broader than Data Professionals.'),('2521','Partial database/data-management tasks; not a Data Analyst equivalent.')]:
                a=ilo[code]
                reps.append({**a,'mapping_quality':'partial_representative','mapping_rationale':rationale})
        else:
            code,quality=CODES[career_id]
            a=ilo[code]
            ilo_primary={**a,'status':'matched_isco_code','mapping_quality':quality,
                         'occupation_mean_score_2025':None}
            reps=[]
        # Source-specific values are deliberately not converted into a unified risk score.
        results.append({
            'career_id':career_id,'career_title':c['title'],'masco_code':c.get('masco_code'),
            'oecd':{
                'status':x['oecd_record_status'],'onet_code':x['onet_code'],
                'occupation_title':x['oecd_occupation_title'],
                'baseline_reversed_normalized_gap_index':x['baseline_ai_exposure_index_0_to_1'],
                'plus_one_cognitive_capability_research_scenario_index':x['oecd_plus_one_cognitive_scenario_index_0_to_1'],
                'mapping_note':x['occupation_mapping_note'],
                'interpretation':'Higher reversed normalized index indicates smaller AI capability gap; not job displacement or a Malaysia-specific rate.',
                'source_id':'src_oecd_ai_exposure_2026'},
            'ilo':{**ilo_primary,'representative_occupations':reps,
                'measurement':'Potential exposure of occupational tasks to generative AI, not predicted job loss.',
                'occupation_mean_score_status':'Not in the provided 4digits_with_tasks.xlsx; do not calculate or label a published mean from this file.',
                'source_id':'src_ilo_genai_exposure_2025'},
            'malaysian_context':{
                'published_ai_impact_label':c.get('ai_impact'),
                'evidence_note':c.get('evidence_notes',{}).get('ai_impact') or c.get('evidence_notes',{}).get('industry_ai_context'),
                'occupation_mapping_note':c.get('occupation_mapping_note'),
                'source_ids':c.get('source_ids',[]),
                'evidence_claim_ids':c.get('evidence_claim_ids',[])},
            'limitations':['The OECD, ILO and TalentCorp assessments use different methods and cannot be averaged.',
                'AI capability overlap and GenAI exposure are not job replacement probabilities.',
                'International occupational evidence is not a measured Malaysian employment or AI-adoption rate.'],
            'display_status':'available_with_mapping_caveat' if career_id!='role_data_professional' else 'representative_evidence_only',
            'overall_ai_risk_score':None
        })
    bundle={
        'dataset':'SkillShift AI six-career source-separated AI exposure evidence',
        'schema_version':'1.0','career_count':6,
        'not_a_job_replacement_probability':True,'does_not_adjust_readiness_scores':True,
        'source_provenance':{
            'ilo':{'title':'Gmyrek et al. 2025 ILO Working Paper 140 / authors dataset',
                   'url':'https://github.com/pgmyrek/2025_GenAI_scores_ISCO08',
                   'input_file':'data/external/ilo/4digits_with_tasks.xlsx','license':'CC BY 4.0',
                   'adaptation_notice':'This is an adaptation of copyrighted ILO material; it has not been prepared, reviewed or endorsed by the ILO.'},
            'oecd':{'title':'OECD AI Capability Gap Index','input_file':'data/processed/oecd_ai_exposure_evidence.json',
                    'doi':oecd_raw.get('doi'),'source_publication_year':oecd_raw.get('source_publication_year')},
            'malaysia':{'title':'TalentCorp and MASCO/eMASCO evidence','input_file':'data/careers.json',
                        'source_reference_file':'data/sources.json'}},
        'careers':results}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: Wrote {len(results)} career profiles to {OUT}')
    for row in results:
        print(row['career_id'],row['ilo']['exposure_category_2025'],row['oecd']['status'])
    return bundle

if __name__=='__main__':build()
