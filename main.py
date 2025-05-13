# main.py
from fastapi import FastAPI
from schemas import CVInput, JobInput, SkillMatchOutput
from tools.skill_matcher import skill_matcher

app = FastAPI()

@app.post("/match_skills", response_model=SkillMatchOutput)
def match_skills(cv: CVInput, job: JobInput):
    return skill_matcher(cv, job)