from __future__ import annotations

import typing as ty
import datetime as dt

import aiohttp
from fastapi import HTTPException
from pydantic import BaseModel

from rfam_batch import api

INFERNAL_CMSCAN_BASE_URL = "https://www.ebi.ac.uk/Tools/services/rest/infernal_cmscan"


class Query:
    sequences: ty.List[str]
    email_address: str
    id: ty.Optional[str]

    def payload(self) -> ty.Dict[str, str]:
        payload = {
            "email": self.email_address,
            "threshold_model": "cut_ga",
            "sequence": self.sequences,
        }
        if self.id:
            payload["title"] = self.id
        return payload


class JobSubmitResult:
    job_id: str


# class FinishedJob:
#     async def infernal_results(self) -> ty.Optional[api.CmScanResult]:
#         try:
#             # Use the JobDispatcher to fetch the status of the job
#             job_status = await JobDispatcher().status(self.job_id)

#             # Check if the job is finished (you can customize this condition)
#             if job_status.status == "done":
#                 # Use the JobDispatcher to fetch the results
#                 results = await JobDispatcher().fetch_results(self.job_id)

#                 # If results are available, create a CmScanResult instance and return it
#                 return api.CmScanResult.build(
#                     closed=results.closed,
#                     search_sequence=results.search_sequence,
#                     hits=results.hits,
#                     opened=results.opened,
#                     num_hits=results.num_hits,
#                     started=results.started,
#                     job_id=results.job_id,
#                 )
#         except Exception as e:
#             # Handle any exceptions or errors during the process
#             print(f"Failed to retrieve infernal results: {str(e)}")

#         # If results are not available or an error occurs, return None
#         return None


class JobDispatcher:
    client: ty.Optional[aiohttp.ClientSession] = None

    @classmethod
    async def startup(cls) -> JobDispatcher:
        if cls.client is None:
            cls.client = aiohttp.ClientSession()
        return cls()

    @classmethod
    async def shutdown(cls) -> None:
        if cls.client:
            await cls.client.close()
        cls.client = None

    async def submit_cmscan_job(self, data: Query) -> str:
        try:
            query = data.payload()
            async with self.client.post(f"{INFERNAL_CMSCAN_BASE_URL}/run", data=query) as r:
                response_text = await r.text()
                return response_text
                # return JobSubmitResult(job_id=response_text)
        except Exception as e:
            print(f"An Exception occurred: {e}")
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {e}"
            )

    async def cmscan_result(self, job_id: str):
        async with self.client.get(f"{INFERNAL_CMSCAN_BASE_URL}/result/{job_id}/out") as r:
            response_text = await r.text()
            return response_text
