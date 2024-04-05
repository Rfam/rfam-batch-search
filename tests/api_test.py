import pytest

from rfam_batch.api import SubmittedRequest


def test_valid_sequence():
    raw_sequence = ">seq1\nACGTU"
    request = SubmittedRequest.parse(raw_sequence)
    assert request.sequence == "ACGTU"


def test_no_fasta_header():
    raw_sequence = "ACGT"
    request = SubmittedRequest.parse(raw_sequence)
    assert request.sequence == "ACGT"


def test_sequence_length_exceeds_limit():
    raw_sequence = "A" * 7001
    with pytest.raises(ValueError):
        SubmittedRequest.parse(raw_sequence)


def test_invalid_characters_in_sequence():
    raw_sequence = "ACGTUXYZ"
    with pytest.raises(ValueError):
        SubmittedRequest.parse(raw_sequence)


def test_gap_characters_in_sequence():
    raw_sequence = "ACGT.U"
    with pytest.raises(ValueError):
        SubmittedRequest.parse(raw_sequence)


def test_valid_nucleotide_sequence():
    raw_sequence = "ACGTURYSWMKBDHN"
    request = SubmittedRequest.parse(raw_sequence)
    assert request.sequence == "ACGTURYSWMKBDHN"


def test_case_insensitivity():
    raw_sequence = "acgturyswmkbdhn"
    request = SubmittedRequest.parse(raw_sequence)
    print(request.sequence)
    assert request.sequence == "ACGTURYSWMKBDHN"


def test_mixed_case_sequence():
    raw_sequence = ">Header\nAcGt"
    request = SubmittedRequest.parse(raw_sequence)
    assert request.sequence == "ACGT"
