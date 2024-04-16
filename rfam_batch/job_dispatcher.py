from __future__ import annotations

import typing as ty

import aiohttp
from fastapi import HTTPException

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
            async with self.client.post(
                f"{INFERNAL_CMSCAN_BASE_URL}/run", data=query
            ) as r:
                response_text = await r.text()
                return response_text
                # return JobSubmitResult(job_id=response_text)
        except Exception as e:
            print(f"An Exception occurred: {e}")
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {e}"
            )

    async def cmscan_result(self, job_id: str) -> str:
        async with self.client.get(
            f"{INFERNAL_CMSCAN_BASE_URL}/result/{job_id}/out"
        ) as r:
            if r.status != 200:
                return ""
            return await r.text()

    async def cmscan_sequence(self, job_id: str) -> str:
        async with self.client.get(
            f"{INFERNAL_CMSCAN_BASE_URL}/result/{job_id}/sequence"
        ) as r:
            if r.status != 200:
                return ""
            return await r.text()

    async def cmscan_tblout(self, job_id: str) -> str:
        async with self.client.get(
            f"{INFERNAL_CMSCAN_BASE_URL}/result/{job_id}/tblout"
        ) as r:
            if r.status != 200:
                return ""
            return await r.text()
