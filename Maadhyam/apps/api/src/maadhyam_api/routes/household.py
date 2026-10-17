"""Transient local household preparation graph. Labels and consent are user claims,
not authentication, legal relationships, identity verification, or permission grants.
"""
from typing import Literal
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, model_validator

router=APIRouter(prefix='/household',tags=['Household preparation'])
class Member(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    id:str=Field(min_length=1,max_length=128)
    label:str=Field(min_length=1,max_length=200)
    createdAt:datetime|None=None
    updatedAt:datetime|None=None
    relationship:Literal['self','parent','guardian','spouse','child','sibling','other']
    dependsOnMemberIds:list[str]=Field(default_factory=list,max_length=30)
    dependsOnDocumentIds:list[str]=Field(default_factory=list,max_length=60)
    relationshipEvidenceDocumentIds:list[str]=Field(default_factory=list,max_length=60)
class Evidence(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id:str=Field(min_length=1,max_length=128)
    memberId:str=Field(min_length=1,max_length=128)
    associationConfirmed:bool=False
    reviewed:bool=False
class HouseholdRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    members:list[Member]=Field(default_factory=list,max_length=30)
    documents:list[Evidence]=Field(default_factory=list,max_length=60)
    @model_validator(mode='after')
    def references(self):
        members={m.id:m for m in self.members}; docs={d.id:d for d in self.documents}
        if len(members)!=len(self.members) or len(docs)!=len(self.documents):raise ValueError('Member and document IDs must be unique')
        if sum(m.relationship=='self' for m in self.members)>1:raise ValueError('Only one applicant label is allowed')
        for d in self.documents:
            if d.memberId not in members:raise ValueError('Unknown document owner')
            if not d.associationConfirmed:raise ValueError('Evidence association requires explicit confirmation')
        for m in self.members:
            if any(i not in members for i in m.dependsOnMemberIds):raise ValueError('Unknown member dependency')
            if any(i not in docs for i in m.dependsOnDocumentIds+m.relationshipEvidenceDocumentIds):raise ValueError('Unknown document dependency or relationship evidence')
        return self

@router.post('/assess')
def assess_household(req:HouseholdRequest):
    nodes=[{'id':'member:'+m.id,'label':m.label,'kind':'member'} for m in req.members]+[{'id':'document:'+d.id,'label':d.id,'kind':'document'} for d in req.documents]
    edges=[]
    for m in req.members:
        edges.extend({'before':'member:'+i,'after':'member:'+m.id,'reason':'member prerequisite'} for i in dict.fromkeys(m.dependsOnMemberIds))
        edges.extend({'before':'document:'+i,'after':'member:'+m.id,'reason':'document prerequisite'} for i in dict.fromkeys(m.dependsOnDocumentIds+m.relationshipEvidenceDocumentIds))
    pending={n['id']:{e['before'] for e in edges if e['after']==n['id']} for n in nodes}
    order=[]
    while pending:
        ready=sorted(i for i,deps in pending.items() if not deps)
        if not ready:break
        order.extend(ready)
        for i in ready:del pending[i]
        for deps in pending.values():deps.difference_update(ready)
    reviewed={d.id for d in req.documents if d.reviewed}
    missing=[m.id for m in req.members if m.relationship!='self' and not any(i in reviewed for i in m.relationshipEvidenceDocumentIds)]
    return {'memberCount':len(req.members),'documentCount':len(req.documents),'dependencyGraph':{'nodes':nodes,'edges':edges,'executionOrder':order,'cycleOrBlockedNodeIds':sorted(pending)},
            'missingRelationshipEvidenceMemberIds':missing,
            'reviewedEvidenceByMember':{m.id:[d.id for d in req.documents if d.memberId==m.id and d.reviewed] for m in req.members},
            'ownershipAssociations':[{'documentId':d.id,'memberId':d.memberId} for d in req.documents],
            'applicantLabelMissing':not any(m.relationship=='self' for m in req.members),
            'officialRelationshipVerified':False,'crossAccountAuthorizationVerified':False,
            'disclaimer':'Local preparation labels and user-confirmed associations only. Relationships and evidence acceptance require official verification. No authentication or cross-account authorization is provided.'}
