from __future__ import annotations

import typing as ty
import datetime as dt

from pydantic import BaseModel, Field

TIMESTAMP_FORMAT = ''

SEARCH_MULTIPLIER = 0


class SubmissionResponse(BaseModel):
    result_url: str = Field(alias='resultURL')
    opened: dt.datetime
    estimated_time: float = Field(alias='estimatedTime')
    job_id: str = Field(alias='jobId')

    @classmethod
    def build(cls) -> SubmissionResponse:
        pass


class SubmittedRequest(BaseModel):
    @classmethod
    def parse(cls, raw: str) -> SubmittedRequest:
        pass


class InfernalAlignment(BaseModel):
    user_seq: str
    hit_seq: str
    ss: str
    match: str
    pp: str
    nc: str


class InfernalHit(BaseModel):
    score: str
    e: str = Field(alias='E')
    acc: str
    end: str
    alignment: InfernalAlignment
    strand: str
    id: str
    gc: str = Field(alias='GC')
    start: str


class CmScanResult(BaseModel):
    closed: dt.datetime
    search_sequence: str = Field(alias='searchSequence')
    hits: ty.Dict[str, InfernalHit]
    opened: dt.datetime
    num_hits: int = Field(alias='numHits')
    started: dt.datetime
    job_id: str = Field(alias='jobId')

    @classmethod
    def build(cls) -> CmScanResult:
        pass
