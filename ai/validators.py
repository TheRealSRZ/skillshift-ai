from pydantic import BaseModel, Field

class CourseSelection(BaseModel):
    course_id: str
    reason: str = Field(min_length=3, max_length=350)

def filter_to_verified_course_ids(course_ids: list[str], resources: list[dict]):
    verified = {r['id'] for r in resources if r.get('verified') and r.get('url')}
    return [cid for cid in course_ids if cid in verified]
