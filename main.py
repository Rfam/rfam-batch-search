#!/usr/bin/env python3

import typing as ty

from fastapi import FastAPI, File, HTTPException, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from rfam_batch import job_dispatcher as jd
from rfam_batch import api

app = FastAPI(docs_url="/docs")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://rfam.org",
    "https://preview.rfam.org",
    "https://rfam.xfam.org",
    "https://batch.rfam.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await jd.JobDispatcher.shutdown()


@app.on_event("startup")
async def on_startup() -> None:
    await jd.JobDispatcher.startup()


@app.get("/result/{job_id}")
async def get_result(job_id: str) -> api.CmScanResult | api.MultipleSequences:
    try:
        out = await jd.JobDispatcher().cmscan_result(job_id)
        sequence = await jd.JobDispatcher().cmscan_sequence(job_id)
        tblout = await jd.JobDispatcher().cmscan_tblout(job_id)
        cm_scan_result = api.parse_cm_scan_result(out, sequence, tblout, job_id)
    except HTTPException as e:
        raise e

    return cm_scan_result


@app.post("/submit-job")
async def submit_job(
    *,
    email_address: ty.Annotated[str, Form()],
    sequence_file: UploadFile = File(...),
    id: ty.Optional[str] = Form(None),
    request: Request,
) -> api.SubmissionResponse:
    url = request.url

    try:
        content = await sequence_file.read()
        parsed = api.SubmittedRequest.parse(content.decode())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    query = jd.Query()
    query.id = id
    query.sequences = parsed.sequences
    query.email_address = email_address

    try:
        job_id = await jd.JobDispatcher().submit_cmscan_job(query)
    except HTTPException as e:
        raise e

    return api.SubmissionResponse.build(
        result_url=f"{url.scheme}://{url.netloc}/result/{job_id}",
        job_id=job_id,
    )


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
