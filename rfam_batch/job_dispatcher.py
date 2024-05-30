from __future__ import annotations

import aiohttp
import httpx
import re
import typing as ty

from fastapi import HTTPException
from logger import logger

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
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{INFERNAL_CMSCAN_BASE_URL}/run", data=query
                )
                response.raise_for_status()
                return response.text
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while requesting {e.request.url!r}: {str(e)}",
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400 and "<description>" in response.text:
                # Extract and display the Job Dispatcher error message, e.g.:
                # <error>
                #  <description>Please enter a valid email address</description>
                # </error>
                text = re.search(
                    r"<description>(.*?)</description>", response.text, re.DOTALL
                )
                logger.error(f"JD error message: {text.group(1)}")
                raise HTTPException(status_code=400, detail=text.group(1))
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Error {e.response.status_code} while requesting "
                    f"{e.request.url!r}: {e.response.text}",
                )
        except httpx.TimeoutException as e:
            raise HTTPException(
                status_code=504, detail=f"Request to {e.request.url!r} timed out."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {str(e)}"
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

    async def cmscan_status(self, job_id: str) -> str:
        async with self.client.get(f"{INFERNAL_CMSCAN_BASE_URL}/status/{job_id}") as r:
            return await r.text()
