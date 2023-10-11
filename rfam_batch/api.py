from __future__ import annotations
import re

import typing as ty
import datetime as dt

from pydantic import BaseModel, Field

TIMESTAMP_FORMAT = ""

SEARCH_MULTIPLIER = 0


class SubmissionResponse(BaseModel):
    result_url: str = Field(alias="resultURL")
    opened: dt.datetime
    estimated_time: float = Field(alias="estimatedTime")
    job_id: str = Field(alias="jobId")

    @classmethod
    def build(
        cls, result_url: str, opened: dt.datetime, estimated_time: float, job_id: str
    ) -> "SubmissionResponse":
        return cls(
            resultURL=result_url,
            opened=opened,
            estimatedTime=estimated_time,
            jobId=job_id,
        )


class SubmittedRequest(BaseModel):
    sequence: str

    @classmethod
    def parse(cls, raw: str) -> SubmittedRequest:
        # Remove FASTA headers and capitalise
        lines = raw.strip().split("\n")
        sequence_lines = [line for line in lines if not line.startswith(">")]
        raw_sequence = "".join(sequence_lines).upper()

        # Check sequence length
        if len(raw_sequence) > 7000:
            raise ValueError("Sequence length must be less than 7,000 nucleotides")

        # Check for invalid characters
        invalid_chars = re.findall(r"[^ACGTURYSWMKBDHN]", raw_sequence.upper())
        if invalid_chars:
            raise ValueError(
                "Invalid characters in sequence: {}".format(", ".join(invalid_chars))
            )

        # Check for gap characters
        if "." in raw_sequence or "-" in raw_sequence:
            raise ValueError("Gap characters '.' and '-' are not allowed")

        # Check if the sequence contains only nucleotide symbols
        valid_nucleotide_symbols = set("ACGTURYSWMKBDHN")
        if not all(char.upper() in valid_nucleotide_symbols for char in raw_sequence):
            raise ValueError("Invalid nucleotide sequence")

        return cls(sequence=raw_sequence)


class InfernalAlignment(BaseModel):
    user_seq: str
    hit_seq: str
    ss: str
    match: str
    pp: str
    nc: str


class InfernalHit(BaseModel):
    score: str
    e: str = Field(alias="E")
    acc: str
    end: str
    alignment: InfernalAlignment
    strand: str
    id: str
    gc: str = Field(alias="GC")
    start: str


class CmScanResult(BaseModel):
    closed: dt.datetime
    search_sequence: str = Field(alias="searchSequence")
    hits: ty.Dict[str, InfernalHit]
    opened: dt.datetime
    num_hits: int = Field(alias="numHits")
    started: dt.datetime
    job_id: str = Field(alias="jobId")

    @classmethod
    def build(
        cls,
        closed: dt.datetime,
        search_sequence: str,
        hits: ty.Dict[str, InfernalHit],
        opened: dt.datetime,
        num_hits: int,
        started: dt.datetime,
        job_id: str,
    ) -> "CmScanResult":
        return cls(
            closed=closed,
            searchSequence=search_sequence,
            hits=hits,
            opened=opened,
            numHits=num_hits,
            started=started,
            jobId=job_id,
        )
