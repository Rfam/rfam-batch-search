import pytest

from rfam_batch.api import Alignment, CmScanResult, Hit, parse_cm_scan_result


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
