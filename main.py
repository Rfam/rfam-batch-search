#!/usr/bin/env python3

import argparse
import datetime as dt
import typing as ty

from fastapi import FastAPI, File, HTTPException, Form, UploadFile
import requests
import uvicorn

from rfam_batch import job_dispatcher as jd
from rfam_batch import api

app = FastAPI(docs_url="/docs")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await jd.JobDispatcher.shutdown()


@app.on_event("startup")
async def on_startup() -> None:
    await jd.JobDispatcher.startup()


@app.get("/result/{job_id}")
async def get_result(job_id: str) -> api.CmScanResult:

    try:
        result = await jd.JobDispatcher().cmscan_result(job_id)
        cm_scan_result = api.parse_cm_scan_result(result) 
    except HTTPException as e:
        raise e

    return cm_scan_result


@app.post("/submit-job")
async def submit_job(
    # sequence: ty.Annotated[str, Form()],
    email_address: ty.Annotated[str, Form()],
    sequence_file: UploadFile = File(...),
    id: ty.Optional[str] = Form(None),
) -> api.SubmissionResponse:
#   ) -> str:
    try:
        content = await sequence_file.read()
        parsed = api.SubmittedRequest.parse(content.decode())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    query = jd.Query()
    query.id = id
    query.sequences = parsed.sequences
    query.email_address = email_address
    # query = jd.Query(sequences=parsed.sequences, email_address=email_address, id=id)

    try:
        job_id = await jd.JobDispatcher().submit_cmscan_job(query)
        print(job_id)
    except HTTPException as e:
        raise e
    
    # return job_id

    return api.SubmissionResponse.build(
        job_id=job_id,
    )


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
