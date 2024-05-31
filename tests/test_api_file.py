import pytest

from rfam_batch.api import *


@pytest.fixture
def out_text():
    with open("example_files/out", "r") as file:
        return file.read()


@pytest.fixture
def sequence():
    with open("example_files/sequence", "r") as file:
        return file.read()


@pytest.fixture
def tblout_text():
    with open("example_files/tblout", "r") as file:
        return file.read()


def test_valid_header():
    assert SubmittedRequest.validate_header(">valid_header") == ">valid_header"


def test_invalid_header():
    with pytest.raises(ValueError, match="Invalid characters in header"):
        SubmittedRequest.validate_header(">invalid;header")
    with pytest.raises(ValueError, match="Invalid characters in header"):
        SubmittedRequest.validate_header(">invalid\\header")
    with pytest.raises(ValueError, match="Invalid characters in header"):
        SubmittedRequest.validate_header(">invalid!header")
    with pytest.raises(ValueError, match="Invalid characters in header"):
        SubmittedRequest.validate_header(">invalid*header")


def test_valid_sequence():
    assert SubmittedRequest.validate_sequence("ACGTU") == "ACGTU"


def test_sequence_invalid_length():
    with pytest.raises(
        ValueError,
        match="Sequence length must be less than or equal to 7,000 nucleotides",
    ):
        SubmittedRequest.validate_sequence("A" * 7001)


def test_sequence_invalid_characters():
    with pytest.raises(ValueError, match="Invalid characters in sequence"):
        SubmittedRequest.validate_sequence("ACGTX")


def test_gap_characters_in_sequence():
    raw_sequence = "ACGT.U"
    with pytest.raises(ValueError):
        SubmittedRequest.parse(raw_sequence)


def test_parse_single_sequence():
    raw_input = ">header1\nACGTACGT"
    result = SubmittedRequest.parse(raw_input)
    assert len(result.sequences) == 1
    assert result.sequences[0] == ">header1\nACGTACGT"


def test_parse_multiple_sequences():
    raw_input = ">header1\nACGT\n>header2\nTGCA"
    result = SubmittedRequest.parse(raw_input)
    assert len(result.sequences) == 2
    assert result.sequences[0] == ">header1\nACGT"
    assert result.sequences[1] == ">header2\nTGCA"


def test_case_insensitivity():
    raw_sequence = "acgturyswmkbdhn"
    request = SubmittedRequest.parse(raw_sequence)
    assert request.sequences[0].strip() == "ACGTURYSWMKBDHN"


def test_mixed_case_sequence():
    raw_sequence = ">Header\nAcGt"
    request = SubmittedRequest.parse(raw_sequence)
    assert request.sequences[0] == ">Header\nACGT"


def test_parse_cm_scan_result_instance(out_text, sequence, tblout_text):
    job_id = "test_job_id"
    result = parse_cm_scan_result(out_text, sequence, tblout_text, job_id)
    assert isinstance(result, CmScanResult)


def test_parse_cm_scan_result_sequence(out_text, sequence, tblout_text):
    job_id = "test_job_id"
    result = parse_cm_scan_result(out_text, sequence, tblout_text, job_id)
    assert (
        result.searchSequence
        == "AGTTACGGCCATACCTCAGAGAATATACCGTATCCCGTTCGATCTGCGAAGTTAAGCTCTGAAGGGCGTCGTCAGTACTATAGTGGGTGACCATATGGGAATACGACGTGCTGTAGCTT"
    )


def test_parse_cm_scan_result_num_hits(out_text, sequence, tblout_text):
    job_id = "test_job_id"
    result = parse_cm_scan_result(out_text, sequence, tblout_text, job_id)
    assert result.numHits == 1


def test_parse_cm_scan_result_date(out_text, sequence, tblout_text):
    job_id = "test_job_id"
    result = parse_cm_scan_result(out_text, sequence, tblout_text, job_id)
    assert result.opened == "2024-04-03 10:28:27"


def test_parse_cm_scan_result_hits(out_text, sequence, tblout_text):
    job_id = "test_job_id"
    result = parse_cm_scan_result(out_text, sequence, tblout_text, job_id)
    hits = {
        "5S_rRNA": [
            Hit(
                id="5S_rRNA",
                acc="RF00001",
                start=1,
                end=119,
                strand="+",
                GC=0.49,
                score=104.9,
                E=4.5e-24,
                alignment=Alignment(
                    nc="#NC                                                                                                                                          ",
                    ss="#SS                  (((((((((,,,,<<-<<<<<---<<--<<<<<<______>>-->>>>-->>---->>>>>-->><<<-<<----<-<<-----<<____>>----->>->-->>->>>))))))))): ",
                    hit_seq="#CM 1 gccuGcggcCAUAccagcgcgaAagcACcgGauCCCAUCcGaACuCcgAAguUAAGcgcgcUugggCcagggUAGUAcuagGaUGgGuGAcCuCcUGggAAgaccagGugccgCaggcc 119",
                    match="#MATCH                  :: U:C:GCCAUACC ::G:GAA ::ACCG AUCCC+U+CGA CU CGAA::UAAGC:C:: +GGGC: :G  AGUACUA  +UGGGUGACC+  UGGGAA+AC:A:GUGC:G:A ::+",
                    user_seq="#SEQ 1 AGUUACGGCCAUACCUCAGAGAAUAUACCGUAUCCCGUUCGAUCUGCGAAGUUAAGCUCUGAAGGGCGUCGUCAGUACUAUAGUGGGUGACCAUAUGGGAAUACGACGUGCUGUAGCUU 119",
                    pp="#PP                  *********************************************************************************************************************** ",
                ),
            )
        ]
    }
    assert result.hits == hits


def test_submission_response_build():
    job_id = "infernal_cmscan-R20240530-111350-0806-24133014-p1m"
    result_url = "https://batch.rfam.org/result/infernal_cmscan-R20240530-111350-0806-24133014-p1m/tblout"
    response = SubmissionResponse.build(job_id, result_url)
    assert response.job_id == job_id
    assert response.result_url == result_url
    assert response.dict(by_alias=True) == {"jobId": job_id, "resultURL": result_url}


def test_submission_response_validation():
    with pytest.raises(ValueError):
        SubmissionResponse(resultURL="https://batch.rfam.org", jobId=None)


def test_submission_response_fields():
    response = SubmissionResponse(
        resultURL="https://batch.rfam.org/result", jobId="1234"
    )
    assert response.job_id == "1234"
    assert response.result_url == "https://batch.rfam.org/result"


def test_multiple_sequences_initialization():
    opened = "2023-05-31 12:00:00"
    hits = [
        {
            "id": "hit1",
            "acc": "acc1",
            "start": 1,
            "end": 100,
            "strand": "+",
            "GC": 50.0,
            "score": 100.0,
            "E": 0.001,
        },
        {
            "id": "hit2",
            "acc": "acc2",
            "start": 101,
            "end": 200,
            "strand": "-",
            "GC": 52.0,
            "score": 200.0,
            "E": 0.002,
        },
    ]
    multiple_sequences = MultipleSequences(opened=opened, hits=hits)
    assert multiple_sequences.opened == opened
    assert len(multiple_sequences.hits) == 2
    assert multiple_sequences.hits[0]["id"] == "hit1"
    assert multiple_sequences.hits[1]["id"] == "hit2"


def test_multiple_sequences_empty_hits():
    opened = "2023-05-31 12:00:00"
    hits = []
    multiple_sequences = MultipleSequences(opened=opened, hits=hits)
    assert multiple_sequences.opened == opened
    assert len(multiple_sequences.hits) == 0
