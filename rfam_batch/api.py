from __future__ import annotations
import re

import typing as ty
import datetime as dt

from pydantic import BaseModel, Field

TIMESTAMP_FORMAT = ""

SEARCH_MULTIPLIER = 0


class SubmissionResponse(BaseModel):
    # result_url: str = Field(alias="resultURL")
    # opened: dt.datetime
    # estimated_time: float = Field(alias="estimatedTime")
    job_id: str = Field(alias="jobId")

    @classmethod
    def build(cls, job_id: str) -> "SubmissionResponse":
        return cls(
            # resultURL=result_url,
            # opened=opened,
            # estimatedTime=estimated_time,
            jobId=job_id,
        )


class SubmittedRequest(BaseModel):
    sequences: ty.List[str]

    @classmethod
    def parse(cls, raw: str) -> SubmittedRequest:
        sequences = []
        current_sequence = ""
        lines = raw.strip().split("\n")

        for line in lines:
            line = line.strip()

            # Check if the line starts with ">"
            if line.startswith(">"):
                if current_sequence:
                    # Remove FASTA headers and apply checks
                    sequence_lines = current_sequence.split("\n")
                    raw_sequence = "".join(sequence_lines).upper()

                    # Check sequence length
                    if len(raw_sequence) > 7000:
                        raise ValueError(
                            "Sequence length must be less than 7,000 nucleotides"
                        )

                    # Check for invalid characters
                    invalid_chars = re.findall(
                        r"[^ACGTURYSWMKBDHN]", raw_sequence.upper()
                    )
                    if invalid_chars:
                        raise ValueError(
                            "Invalid characters in sequence: {}".format(
                                ", ".join(invalid_chars)
                            )
                        )

                    # Check for gap characters
                    if "." in raw_sequence or "-" in raw_sequence:
                        raise ValueError("Gap characters '.' and '-' are not allowed")

                    # Add the validated sequence to the list
                    sequences.append(raw_sequence)
                current_sequence = ""
            else:
                current_sequence += line

        # Add the last sequence to the list after the loop
        if current_sequence:
            # Apply checks to the last sequence
            sequence_lines = current_sequence.split("\n")
            raw_sequence = "".join(sequence_lines).upper()

            # Check sequence length
            if len(raw_sequence) > 7000:
                raise ValueError("Sequence length must be less than 7,000 nucleotides")

            # Check for invalid characters
            invalid_chars = re.findall(r"[^ACGTURYSWMKBDHN]", raw_sequence.upper())
            if invalid_chars:
                raise ValueError(
                    "Invalid characters in sequence: {}".format(
                        ", ".join(invalid_chars)
                    )
                )

            # Check for gap characters
            if "." in raw_sequence or "-" in raw_sequence:
                raise ValueError("Gap characters '.' and '-' are not allowed")

            # Add the validated last sequence to the list
            sequences.append(raw_sequence)

        return cls(sequences=sequences)

class HitAlignment(BaseModel):
    rank: int
    e_value: float
    score: float
    bias: float
    model_name: str
    start: int
    end: int
    mdl: str
    trunc: str
    gc: float
    description: str

class Hit(BaseModel):
    rank: int
    e_value: float
    score: float
    bias: float
    model_name: str
    start: int
    end: int
    mdl: str
    trunc: str
    gc: float
    description: str

class Alignment(BaseModel):
    sequence_name: str
    sequence: str
    model_name: str
    sequence_start: int
    sequence_end: int
    model_start: int
    model_end: int
    acc: float
    trunc: str
    gc: float

class CmScanResult(BaseModel):
    query: str
    hit_scores: ty.List[Hit]
    hit_alignments: ty.List[Alignment]

# Function to parse the CmScanResult format into the models
def parse_cm_scan_result(result_text: str) -> CmScanResult:
    lines = result_text.split('\n')
    query = lines[9].split()[-1]

    # Initialize empty lists for hit_scores and hit_alignments
    hit_scores = []
    hit_alignments = []

    # Iterate through lines to extract data
    line_index = 12  # Start of hit scores
    while line_index < len(lines):
        if lines[line_index].startswith('>>'):
            line_index += 1  # Skip the header line
            while line_index < len(lines) and not lines[line_index].strip().startswith("rank"):
                parts = lines[line_index].strip().split()
                if len(parts) == 11:
                    rank, e_value, score, bias, model_name, start, end, mdl, trunc, gc, description = parts
                    hit_scores.append(Hit(
                        rank=int(rank),
                        e_value=float(e_value),
                        score=float(score),
                        bias=float(bias),
                        model_name=model_name,
                        start=int(start),
                        end=int(end),
                        mdl=mdl,
                        trunc=trunc,
                        gc=float(gc),
                        description=description,
                    ))
                line_index += 1
        elif lines[line_index].startswith("rank"):
            line_index += 1  # Skip the header line
            while line_index < len(lines) and not lines[line_index].strip().startswith(">>"):
                parts = lines[line_index].strip().split()
                if len(parts) == 10:
                    rank, e_value, score, bias, model_name, mdl_from, mdl_to, seq_from, seq_to, acc = parts
                    sequence_name, model_name = lines[line_index].strip().split("  ")
                    model_name = model_name.strip()
                    sequence_name = sequence_name.strip()
                    alignment = Alignment(
                        sequence_name=sequence_name,
                        sequence=lines[line_index + 1].strip(),
                        model_name=model_name,
                        sequence_start=int(seq_from),
                        sequence_end=int(seq_to),
                        model_start=int(mdl_from),
                        model_end=int(mdl_to),
                        acc=float(acc),
                        trunc="no",
                        gc=0.0,
                    )
                    hit_alignments.append(alignment)
                line_index += 2
        else:
            line_index += 1

    return CmScanResult(query=query, hit_scores=hit_scores, hit_alignments=hit_alignments)



# class InfernalAlignment(BaseModel):
#     user_seq: str
#     hit_seq: str
#     ss: str
#     match: str
#     pp: str
#     nc: str


# class InfernalHit(BaseModel):
#     score: str
#     e: str = Field(alias="E")
#     acc: str
#     end: str
#     alignment: InfernalAlignment
#     strand: str
#     id: str
#     gc: str = Field(alias="GC")
#     start: str


# class CmScanResult(BaseModel):
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
