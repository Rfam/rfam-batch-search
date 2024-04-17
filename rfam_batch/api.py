from __future__ import annotations
import re
import typing as ty

from datetime import datetime
from pydantic import BaseModel, Field

TIMESTAMP_FORMAT = ""

SEARCH_MULTIPLIER = 0


class SubmissionResponse(BaseModel):
    result_url: str = Field(alias="resultURL")
    # opened: dt.datetime
    # estimated_time: float = Field(alias="estimatedTime")
    job_id: str = Field(alias="jobId")

    @classmethod
    def build(cls, job_id: str, result_url: str) -> "SubmissionResponse":
        return cls(
            resultURL=result_url,
            # opened=opened,
            # estimatedTime=estimated_time,
            jobId=job_id,
        )


class SubmittedRequest(BaseModel):
    sequences: ty.List[str]

    @classmethod
    def validate(cls, sequence: str) -> str:
        # Remove FASTA headers and apply checks
        sequence_lines = sequence.split("\n")
        raw_sequence = "".join(sequence_lines).upper()

        # Check sequence length
        if len(raw_sequence) > 7000:
            raise ValueError("Sequence length must be less than 7,000 nucleotides")

        # Check for invalid characters
        invalid_chars = re.findall(r"[^ACGTURYSWMKBDHN]", raw_sequence.upper())
        if invalid_chars:
            raise ValueError(
                f"Invalid characters in sequence: {', '.join(invalid_chars)}"
            )

        # Check for gap characters
        if "." in raw_sequence or "-" in raw_sequence:
            raise ValueError("Gap characters '.' and '-' are not allowed")

        return raw_sequence

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
                    raw_sequence = cls.validate(current_sequence)
                    sequences.append(raw_sequence)
                current_sequence = ""
            else:
                current_sequence += line

        # Add the last sequence to the list after the loop
        if current_sequence:
            raw_sequence = cls.validate(current_sequence)
            sequences.append(raw_sequence)

        return cls(sequences=sequences)


class Alignment(BaseModel):
    nc: str
    ss: str
    hit_seq: str
    match: str
    user_seq: str
    pp: str


class Hit(BaseModel):
    id: str
    acc: str
    start: int
    end: int
    strand: str
    GC: float
    score: float
    E: float
    alignment: Alignment


class CmScanResult(BaseModel):
    searchSequence: str
    numHits: int
    jobId: str
    opened: str
    started: str
    closed: str
    hits: ty.Dict[str, ty.List[Hit]]


class MultipleSequences(BaseModel):
    opened: str
    hits: ty.List


def parse_tblout_file(tblout_text: str) -> ty.Tuple[str, ty.List]:
    """
    This function parses the tblout file and extracts the necessary data
    :param tblout_text: tblout file contents
    :return: date and hit list
    """
    date = ""
    hit_list = []

    for line in tblout_text.split("\n"):
        if not line.startswith("#") and not line == "":
            line = re.sub(" +", " ", line).strip().split(" ")
            hit_list.append(
                {
                    "id": line[0],
                    "acc": line[1],
                    "start": int(line[7]),
                    "end": int(line[8]),
                    "strand": line[9],
                    "GC": float(line[12]),
                    "score": float(line[14]),
                    "E": float(line[15]),
                }
            )
        elif line.startswith("# Date:"):
            date_str = line.split("# Date:")[1].strip()
            date_obj = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y")
            date = date_obj.strftime("%Y-%m-%d %H:%M:%S")

    return date, hit_list


def parse_cm_scan_result(
    out_text: str, sequence: str, tblout_text: str, job_id: str
) -> CmScanResult | MultipleSequences:
    """
    Function to parse the CmScanResult/MultipleSequences format into the models
    :param out_text: out file contents
    :param sequence: sequence file contents
    :param tblout_text: tblout file contents
    :param job_id: ID created by Infernal cmscan
    :return: CmScanResult or MultipleSequences
    """
    if sequence.count(">") > 1:
        # Show only tblout file results
        date, hit_list = parse_tblout_file(tblout_text)
        return MultipleSequences(opened=date, hits=hit_list)

    # Get sequence
    search_sequence = sequence.split("\n")
    if search_sequence[0].startswith(">"):
        search_sequence = "".join(search_sequence[1:])
    else:
        search_sequence = "".join(search_sequence)

    # Get data from tblout_text
    date, hit_list = parse_tblout_file(tblout_text)
    closed = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if date != "" else ""

    # Get number of CM hits reported
    num_hits = re.search(r"Total CM hits reported:\s+(\d+)\s", out_text)
    num_hits = int(num_hits.group(1)) if num_hits else 0

    # Iterate through lines to extract alignment from out_text
    lines = out_text.split("\n")
    line_index = 16  # Start of hit scores
    while line_index < len(lines):
        if lines[line_index].startswith(">>"):
            line_index += 3  # Skip unnecessary lines
            fields = lines[line_index].strip().split()
            start = int(fields[9])
            end = int(fields[10])
            score = float(fields[3])
            e_value = float(fields[2])

            line_index += 2  # Start of alignment
            # Alignments have a fixed number of lines, 6 in total
            alignment = Alignment(
                nc="#NC " + lines[line_index].split("NC")[0],
                ss="#SS " + lines[line_index + 1].split("CS")[0],
                hit_seq="#CM " + " ".join(lines[line_index + 2].split()[1:]),
                match="#MATCH " + lines[line_index + 3],
                user_seq="#SEQ " + " ".join(lines[line_index + 4].split()[1:]),
                pp="#PP " + lines[line_index + 5].split("PP")[0],
            )
            line_index += 6  # End of alignment

            for item in hit_list:
                if (
                    item["start"] == start
                    and item["end"] == end
                    and item["score"] == score
                    and item["E"] == e_value
                ):
                    item["alignment"] = alignment
                    break

        elif lines[line_index] == "Internal CM pipeline statistics summary:":
            # No more alignments to check
            break

        else:
            line_index += 1

    # Rearrange hits according to the pattern expected by the user
    hits = {}
    for item in hit_list:
        id_value = item["id"]
        if id_value not in hits:
            hits[id_value] = []

        hits[id_value].append(Hit(**item))

    return CmScanResult(
        searchSequence=search_sequence,
        numHits=num_hits,
        jobId=job_id,
        opened=date,
        started=date,
        closed=closed,
        hits=hits,
    )
