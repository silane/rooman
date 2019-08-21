import asyncio
import uuid

from . import errors


class Job:
    async def on_action(self, job_action_free_parameter):
        return None

    async def on_delete(self):
        pass


class RoomanBase:
    def __init__(self):
        self.jobs = {}

    async def do_action(self, action_id, action_free_parameter):
        raise NotImplementedError()

    async def do_create_job(self, job_type_id, new_job_free_parameter):
        raise NotImplementedError()

    async def invoke_action(self, action_id, action_free_parameter):
        return await self.do_action(action_id, action_free_parameter)

    async def new_job(self, job_type_id, new_job_free_parameter):
        job = await self.do_create_job(job_type_id, new_job_free_parameter)
            
        while True:
            new_job_id = str(uuid.uuid1())
            if new_job_id not in self.jobs:
                break

        self.jobs[new_job_id] = (job_type_id, job)
        return new_job_id

    async def delete_job(self, job_id):
        job = self.jobs.get(job_id)
        if job is None:
            raise errors.JobIDNotFoundError(job_id)

        await job[1].on_delete()

        del self.jobs[job_id]

    async def list_job(self, job_type_id):
        ret = ((job_id, job_type_id) for job_id, (job_type_id, _) in self.jobs.items())
        if job_type_id is not None:
            ret = (x for x in ret if x[1] == job_type_id)
        return [{'job_id': x[0], 'job_type_id': x[1]} for x in ret]

    async def invoke_job_action(self, job_id, job_action_free_parameter):
        job = self.jobs.get(job_id)
        if job is None:
            raise errors.JobIDNotFoundError(job_id)

        response = await job[1].on_action(job_action_free_parameter)
        return response
