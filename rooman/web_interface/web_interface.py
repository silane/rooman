import threading
import asyncio
import json
from http import HTTPStatus

from threading_utils.request_response_pipe import (
    RequestResponsePipe, RequestEmpty)

from rooman import structured_query
from rooman import core
#from rooman import core.errors
from . import errors


class RoomanWebInterface:
    class ActionRequest:
        def __init__(self, action_id, action_parameter):
            self.action_id = action_id
            self.action_parameter = action_parameter

    class NewJobRequest:
        def __init__(self, job_type_id, new_job_parameter):
            self.job_type_id = job_type_id
            self.new_job_parameter = new_job_parameter

    class DeleteJobRequest:
        def __init__(self, job_id):
            self.job_id = job_id

    class ListJobRequest:
        def __init__(self, job_type_id):
            self.job_type_id = job_type_id

    class JobActionRequest:
        def __init__(self, job_id, job_action_parameter):
            self.job_id = job_id
            self.job_action_parameter = job_action_parameter

    class Response:
        def __init__(self, http_status_code, code, payload):
            self.http_status_code = http_status_code
            self.code = code
            self.payload = payload

    def __init__(self, rooman):
        self.rooman = rooman
        self.pipe = RequestResponsePipe()
        self.request_handle_loop_thread = None

    def wsgi_handler(self, environ, start_response):
        def try_get_key(query, key_name):
            try:
                return True, query[key_name]
            except KeyError:
                return False, None

        def get_key(query, key_name, key_type):
            try:
                k = query[key_name]
            except KeyError:
                raise errors.ParameterMissingAPIError([key_name])
            if not isinstance(k, key_type):
                raise errors.ParameterFormatAPIError([key_name])
            return k

        pipe = self.pipe
        path = environ['PATH_INFO']
        query_string = environ['QUERY_STRING']
        query = structured_query.parse(query_string)

        free_parameter_missing = False
        try:
            if not isinstance(query, dict):
                raise errors.ParameterFormatAPIError([])
            if path == '/action':
                action_id = get_key(query, 'id', str)
                parameter_exists, parameter = try_get_key(query, 'parameters')
                free_parameter_missing = not parameter_exists
                request = self.ActionRequest(action_id, parameter)
            elif path == '/newjob':
                job_type_id = get_key(query, 'type_id', str)
                parameter_exists, parameter = try_get_key(query, 'parameters')
                free_parameter_missing = not parameter_exists
                request = self.NewJobRequest(job_type_id, parameter)
            elif path == '/deletejob':
                job_id = get_key(query, 'id', str)
                request = self.DeleteJobRequest(job_id)
            elif path == '/listjob':
                job_type_id = query.get('type_id')
                if not isinstance(job_type_id, str):
                    job_type_id = None
                request = self.ListJobRequest(job_type_id)
            elif path == '/jobaction':
                job_id = get_key(query, 'id', str)
                parameter_exists, parameter = try_get_key(query, 'parameters')
                free_parameter_missing = not parameter_exists
                request = self.JobActionRequest(job_id, parameter)
            else:
                raise errors.PathNotFoundAPIError(path)
            
            response = pipe.request(request)

            # `core` module cannot distiguish free parameter missing or
            # free parameter is just single value `None`.
            # So here, we are distinguishing these two appropriately.
            if isinstance(response, errors.FreeParameterAPIError):
                if free_parameter_missing and any(not case.path and
                        isinstance(case.error_category,
                                   core.errors.FreeParameterTypeErrorCategory)
                        for case in response.errors):
                    raise errors.ParameterMissingAPIError(['parameters'])

            if isinstance(response, errors.APIError):
                raise response
            
            response = self.Response(
                200, 'success', response,
            )
        except errors.APIError as e:
            response = self.Response(
                e.get_http_status_code(), e.get_code(), e.get_payload(),
            )
        response_code = response.http_status_code
        phrase = next(
            (x.phrase for x in HTTPStatus if x == response_code), '')

        header = [
            ('Content-type', 'application/json; charset=utf-8'),
        ]
        start_response('{} {}'.format(response_code, phrase), header)
        return [json.dumps(
            {'code': response.code, 'payload': response.payload},
            ensure_ascii=False).encode('utf-8')]
    
    def start_request_handle_loop(self):
        if (self.request_handle_loop_thread is not None and
                self.request_handle_loop_thread.is_alive()):
            raise RuntimeError()

        self.request_handle_loop_thread = threading.Thread(
            target=lambda: self.request_handle_loop())
        self.request_handle_loop_thread.start()
    
    def stop_request_handle_loop(self):
        if (self.request_handle_loop_thread is None or
                not self.request_handle_loop_thread.is_alive()):
            raise RuntimeError()

        if self.request_handle_loop_thread is not None:
            self.pipe.request(None)
            self.request_handle_loop_thread.join()
        self.request_handle_loop_thread = None

    def request_handle_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def main_coroutine():
            pipe = self.pipe
            while True:
                try:
                    request, respond = await loop.run_in_executor(
                        None, lambda: pipe.handle_request())
                except RequestEmpty:
                    continue
                
                if request is None:
                    respond(None)
                    break

                try:
                    response = await self.handle_request(request)
                except errors.APIError as e:
                    response = e

                respond(response)

        loop.run_until_complete(main_coroutine())

    async def handle_request(self, request):
        try:
            if isinstance(request, self.ActionRequest):
                ret = await self.rooman.invoke_action(
                    request.action_id, request.action_parameter)
            elif isinstance(request, self.NewJobRequest):
                ret = await self.rooman.new_job(request.job_type_id,
                                                request.new_job_parameter)
            elif isinstance(request, self.DeleteJobRequest):
                ret = await self.rooman.delete_job(request.job_id)
            elif isinstance(request, self.ListJobRequest):
                ret = await self.rooman.list_job(request.job_type_id)
            elif isinstance(request, self.JobActionRequest):
                ret = await self.rooman.invoke_job_action(
                    request.job_id, request.job_action_parameter)
            else:
                raise RuntimeError()
        except core.errors.ActionIDNotFoundError as e:
            raise errors.ActionIDNotFoundAPIError(e.target) from e
        except core.errors.JobTypeIDNotFoundError as e:
            raise errors.JobTypeIDNotFoundAPIError(e.target) from e
        except core.errors.JobIDNotFoundError as e:
            raise errors.JobIDNotFoundAPIError(e.target) from e
        except core.errors.NewJobFreeParameterError as e:
            raise errors.NewJobFreeParameterAPIError(e.errors) from e
        except core.errors.JobActionFreeParameterError as e:
            raise errors.JobActionFreeParameterAPIError(e.errors) from e
        except core.errors.RuntimeRoomanError as e:
            raise errors.RuntimeAPIError(e.detail) from e
        return ret
