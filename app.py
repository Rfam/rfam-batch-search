from fastapi import FastAPI, Form, HTTPException
import typing as ty
import httpx
from pydantic import BaseModel

app = FastAPI()

INFERNAL_CMSCAN_BASE_URL = "https://www.ebi.ac.uk/Tools/services/rest/infernal_cmscan"

job_info = {}


class Data(BaseModel):
    sequence: str
    email_address: str

    def payload(self) -> ty.Dict[str, str]:
        payload = {
            "email": self.email_address,
            "threshold_model": "cut_ga",
            "sequence": self.sequence,
        }
        return payload


async def submit_job_to_jd(data: Data):
    try:
        query = data.payload()
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{INFERNAL_CMSCAN_BASE_URL}/run", data=query)
            response.raise_for_status()
            response_data = response.json()
            print(response_data)
            if response.status_code == 200:
                if "jobId" in response_data:
                    job_id = response_data["jobId"]
                    return job_id
                else:
                    raise HTTPException(status_code=400, detail="Job submission failed")
            else:
                raise HTTPException(
                    status_code=response.status_code, detail=response_data
                )
    except httpx.HTTPError as e:
        print(f"HTTP Error: {e}")
        return {"error": f"An error occurred: {e}"}
    except Exception as e:
        print(f"An Exception occurred: {e}")
        return {"error": f"An unexpected error occurred: {e}"}


@app.post("/submit-job")
async def submit_job(
    sequence: ty.Annotated[str, Form()], email_address: ty.Annotated[str, Form()]
):
    job_id = await submit_job_to_jd(
        Data(sequence=sequence, email_address=email_address)
    )
    return {"jobId": job_id}


@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    if job_id in job_info:
        return job_info[job_id]
    else:
        raise HTTPException(status_code=404, detail="Job ID not found")


@app.get("/job-result/{job_id}")
async def get_job_result(job_id: str):
    if job_id not in job_info:
        raise HTTPException(status_code=404, detail="Job ID not found")

    job_status = job_info[job_id]["status"]

    if job_status == "FINISHED":
        result_url = f"{INFERNAL_CMSCAN_BASE_URL}/{job_id}/result"
        async with httpx.AsyncClient() as client:
            response = await client.get(result_url)

        return response.json()
    else:
        raise HTTPException(status_code=400, detail="Job is not yet completed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
