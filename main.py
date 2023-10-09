#!/usr/bin/env python3

import typing as ty

from fastapi import FastAPI, HTTPException, Form

from rfam_batch import job_dispatcher as jd
from rfam_batch import api

app = FastAPI(docs_url="/docs")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await jd.JobDispatcher.shutdown()


@app.on_event("startup")
async def on_startup() -> None:
    await jd.JobDispatcher.startup()


@app.get("/{uuid}")
async def get_result(job_id: str) -> api.CmScanResult:
    status = jd.JobDispatcher().status(job_id)
    return api.CmScanResult.build(status)


@app.post("/", status_code=202, response_model_by_alias=True)
async def submit_job(sequence: ty.Annotated[str, Form()]) -> api.SubmissionResponse:
    try:
        parsed = api.SubmittedRequest.parse(sequence)
    except:
        raise HTTPException(status_code=502, detail="Invalid FASTA file")

    try:
        info = await jd.JobDispatcher().cmscan(parsed)
    except:
        raise HTTPException(status_code=503, detail="Failed to submit job")

    return api.SubmissionResponse.build(info)
