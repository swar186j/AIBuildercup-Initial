"""Local-first, hypothetical multi-authority planning. No government acceptance claims."""
from __future__ import annotations
from datetime import date, timedelta
from itertools import product
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Literal

class Option(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    costINR: int = Field(ge=0)
    durationDays: int = Field(ge=0)
    visits: int = Field(ge=0)
    authority: str = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    onlinePossible: bool = False
    officialEligibilityVerified: bool = False
    model_config = ConfigDict(extra="forbid")

class Issue(BaseModel):
    id: str = Field(min_length=1)
    options: list[Option] = Field(min_length=1, max_length=8)
    model_config = ConfigDict(extra="forbid")

class PlanningRequest(BaseModel):
    issues: list[Issue] = Field(default_factory=list, max_length=12)
    targetDate: date | None = None
    model_config = ConfigDict(extra="forbid")
    weights: dict[Literal['cost','days','visits'], float] = Field(default_factory=lambda: {'cost':1,'days':1,'visits':1})
    @model_validator(mode='after')
    def unique_ids(self):
        ids = [x.id for x in self.issues]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate issue IDs')
        for issue in self.issues:
            option_ids = [x.id for x in issue.options]
            if len(option_ids) != len(set(option_ids)):
                raise ValueError('Duplicate option IDs')
            if any(x not in ids for option in issue.options for x in option.prerequisites):
                raise ValueError('Unknown prerequisite issue')
        return self

def _topology(selected: dict[str, Option]):
    pending = {key: set(option.prerequisites) for key, option in selected.items()}
    order = []
    while pending:
        ready = sorted(key for key, deps in pending.items() if not deps)
        if not ready:
            return None
        for key in ready:
            order.append(key)
            del pending[key]
        for deps in pending.values():
            deps.difference_update(ready)
    return order

def plan(req: PlanningRequest) -> dict:
    """Enumerate candidate paths; sequential duration is a conservative estimate."""
    best = None
    feasible = 0
    for combination in product(*(issue.options for issue in req.issues)):
        selected = dict(zip((issue.id for issue in req.issues), combination))
        order = _topology(selected)
        if order is None:
            continue
        feasible += 1
        cost = sum(x.costINR for x in combination)
        days = sum(x.durationDays for x in combination)
        visits = sum(x.visits for x in combination)
        score = (req.weights.get('cost',1)*cost/1000 + req.weights.get('days',1)*days + req.weights.get('visits',1)*visits*3)
        candidate = (score, cost, days, visits, tuple(x.id for x in combination), order, selected)
        if best is None or candidate[:5] < best[:5]:
            best = candidate
    if best is None:
        return {'status':'deadlock' if req.issues else 'empty','candidatePathsEvaluated':feasible,
                'cycleDetected':bool(req.issues),'officialAcceptanceVerified':False,
                'message':'No acyclic combination of the supplied hypothetical options exists.'}
    _, cost, days, visits, _, order, selected = best
    remaining = (req.targetDate - date.today()).days if req.targetDate else None
    return {'status':'planned','candidatePathsEvaluated':feasible,
            'selectedOptions':[{'issueId':key,**selected[key].model_dump()} for key in order],
            'totalCostINR':cost,'estimatedSequentialDays':days,'estimatedVisits':visits,
            'potentialOnlineSteps':[key for key in order if selected[key].onlinePossible],
            'targetDate':req.targetDate.isoformat() if req.targetDate else None,
            'daysUntilTarget':remaining,
            'targetFeasibleUnderAssumptions':None if remaining is None else days<=remaining,
            'officialAcceptanceVerified':False,'officialProcessingTimesVerified':False,
            'disclaimer':'Scenario-only optimization using user-supplied assumptions. Verify official eligibility, authority requirements, appointments, processing times and online availability.'}
