#!/usr/bin/env python3
import aiosmtplib
import asyncio
import os
import typing as ty

from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    Form,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
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

# Load environment variables from .env file
load_dotenv()


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


@app.get("/result/{job_id}/tblout", response_class=PlainTextResponse)
async def get_tblout(job_id: str) -> PlainTextResponse:
    try:
        tblout = await jd.JobDispatcher().cmscan_tblout(job_id)
    except HTTPException as e:
        raise e

    # Create a PlainTextResponse with CORS headers
    response = PlainTextResponse(content=tblout)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"

    return response


@app.get("/status/{job_id}", response_class=PlainTextResponse)
async def fetch_status(job_id: str) -> PlainTextResponse:
    try:
        status = await jd.JobDispatcher().cmscan_status(job_id)
    except HTTPException as e:
        raise e

    # Create a PlainTextResponse with CORS headers
    response = PlainTextResponse(content=status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"

    return response


async def send_email(email_address: str, job_id: str, status: str, tblout: str):
    sender_email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    server = os.getenv("SERVER")
    port = os.getenv("PORT")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email_address

    if status == "FINISHED":
        msg["Subject"] = f"Results for batch search job {job_id}"
        msg.attach(MIMEText(tblout, "plain"))
    else:
        msg["Subject"] = f"Error in batch search job {job_id}"
        body = (
            "There was a problem while running the search. Please try "
            "again or send us the job id if the problem persists."
        )
        msg.attach(MIMEText(body, "plain"))

    async with aiosmtplib.SMTP(hostname=server, port=port) as smtp:
        await smtp.login(sender_email, password)
        await smtp.send_message(msg)


async def check_status(email_address: str, job_id: str):
    while True:
        # This function will run as long as the status is 'RUNNING' or 'QUEUED'
        status = await jd.JobDispatcher().cmscan_status(job_id)
        if status == "FINISHED":
            tblout = await jd.JobDispatcher().cmscan_tblout(job_id)
            await send_email(email_address, job_id, status, tblout)
            break
        elif status == "NOT_FOUND":
            # I'm assuming we will never see this status after a POST
            break
        elif status == "FAILURE" or status == "ERROR":
            await send_email(email_address, job_id, status, "")
            break
        await asyncio.sleep(10)


@app.post("/submit-job")
async def submit_job(
    *,
    email_address: ty.Annotated[str, Form()],
    sequence_file: UploadFile = File(...),
    id: ty.Optional[str] = Form(None),
    request: Request,
    background_tasks: BackgroundTasks,
) -> api.SubmissionResponse:
    url = request.url

    try:
        content = await sequence_file.read()
        parsed = api.SubmittedRequest.parse(content.decode())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    query = jd.Query()
    query.id = id
    query.sequences = "\n".join(parsed.sequences)
    query.email_address = email_address

    try:
        job_id = await jd.JobDispatcher().submit_cmscan_job(query)
    except HTTPException as e:
        raise e

    # Background task to check status
    background_tasks.add_task(check_status, email_address, job_id)

    return api.SubmissionResponse.build(
        result_url=f"{url.scheme}://{url.netloc}/result/{job_id}",
        job_id=job_id,
    )


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
