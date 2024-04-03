from __future__ import annotations
import re

import typing as ty
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


class Hit(BaseModel):
    id: str
    acc: str
    start: int
    end: int
    strand: str
    GC: float
    score: float
    E: float
    alignment: str


class CmScanResult(BaseModel):
    searchSequence: str
    numHits: int
    jobId: str
    hits: ty.List[Hit]


# Function to parse the CmScanResult format into the models
def parse_cm_scan_result(out_text: str, sequence: str, tblout_text: str, job_id: str) -> CmScanResult:
    # Get sequence
    search_sequence = sequence.split("\n")
    if search_sequence[0].startswith(">"):
        search_sequence = "".join(search_sequence[1:])
    else:
        search_sequence = "".join(search_sequence)

    # Get data from tblout_text
    tblout = []
    for line in tblout_text.split('\n'):
        if not line.startswith("#") and not line == "":
            line = re.sub(" +", " ", line).strip().split(" ")
            tblout.append({
                "id": line[0],
                "acc": line[1],
                "start": int(line[7]),
                "end": int(line[8]),
                "strand": line[9],
                "GC": float(line[12]),
                "score": float(line[14]),
                "E": float(line[15]),
            })

    # Get number of CM hits reported
    num_hits = re.search(r"Total CM hits reported:\s+(\d+)\s", out_text)
    num_hits = int(num_hits.group(1)) if num_hits else 0

    # Initialize empty lists for hits
    hit_scores = []

    # Iterate through lines to extract alignment from out_text
    lines = out_text.split('\n')
    line_index = 16  # Start of hit scores
    while line_index < len(lines):
        if lines[line_index].startswith(">>"):
            line_index += 3  # Skip unnecessary lines
            fields = lines[line_index].strip().split()
            start = int(fields[9])
            end = int(fields[10])
            score = float(fields[3])
            e_value = float(fields[2])

            alignment = ""
            line_index += 1

            while line_index < len(lines) and not lines[line_index].strip().startswith(">>") and not lines[line_index].strip().startswith("Internal"):
                alignment = alignment + lines[line_index] + "\n"
                line_index += 1

            for item in tblout:
                if item["start"] == start and item["end"] == end and item["score"] == score and item["E"] == e_value:
                    item["alignment"] = alignment
                    hit_scores.append(Hit.model_validate(item))
                    break

        else:
            line_index += 1

    return CmScanResult(searchSequence=search_sequence, numHits=num_hits, jobId=job_id, hits=hit_scores)
