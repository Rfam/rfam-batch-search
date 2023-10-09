from __future__ import annotations

import typing as ty

import aiohttp

DISPATCHER_URL = 'https://www.ebi.ac.uk/Tools/services/rest/infernal_cmscan'

class Query:
    id: ty.Optional[str]
    sequence: str
    email_address: str

    def payload(self) -> ty.Dict[str, str]:
        payload = {
            'email': self.email_address,
            'threshold_model': 'cut_ga',
            'sequence': self.sequence,
        }
        if self.id:
            payload['title'] = self.id
        return payload


class JobSubmitResult:
    job_id: str


class FinishedJob:
    async def infernal_results(self) -> ty.Optional[InfernalResult]:
        pass


class JobDispatcher:
    client: ty.Optional[aiohttp.ClientSession]

    @classmethod
    async def startup(cls) -> JobDispatcher:
        return cls(aiohttp.ClientSession)

    @classmethod
    async def shutdown(cls) -> None:
        if cls.client:
            await cls.client.close()
        cls.client = None

    async def cmscan(self, query: Query) -> JobSubmitResult:
        async with self.client.post(f'{DISPATCHER_URL}/run', data=query.payload()) as r:
            return JobSubmitResult(r.text())

    async def status(self, job_id: str) -> JobStatus:
        async with self.client.get(f'{DISPATCHER_URL}/status/{job_id}') as r:
            raw = r.text()

