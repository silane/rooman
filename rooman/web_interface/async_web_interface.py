import asyncio
import json

from rooman import structured_query
from rooman import core
from . import errors


class RoomanAsyncWebInterface:
    def __init__(self, rooman):
        self.rooman = rooman
        
    async def asgi_handler(self, scope, receive, send):
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

        async def read_body():
            body, more_body = b'', True
            while more_body:
                message = await receive()
                body += message.get('body', b'')
                more_body = message.get('more_body', False)
            return body

        async def respond(http_code, code, payload):
            header = [
                (b'Content-type', b'application/json; charset=utf-8'),
            ]
            body = json.dumps(
                {'code': code, 'payload': payload},
                ensure_ascii=False).encode('utf-8')
            await send({
                'type': 'http.response.start',
                'status': http_code,
                'headers': header,
            })
            await send({
                'type': 'http.response.body',
                'body': body
            })

        assert scope['type'] == 'http'

        path = scope['path']
        
        body = await read_body()
        if body and not body.isspace():
            try:
                body = body.decode('utf-8')
                query = json.loads(body)
            except UnicodeError:
                await respond(400, 'invalid_body', 'encoding')
                return
            except json.JSONDecodeError:
                await respond(400, 'invalid_body', 'json')
                return
        else:
            query_string = scope['query_string']
            query = structured_query.parse(query_string)

        free_parameter_missing = False
        http_code, code, payload = None, None, None
        try:
            try:
                if path == '/action':
                    action_id = get_key(query, 'id', str)
                    parameter_exists, parameter = try_get_key(query,
                                                              'parameters')
                    free_parameter_missing = not parameter_exists
                    response = await self.rooman.invoke_action(action_id,
                                                               parameter)
                elif path == '/newjob':
                    job_type_id = get_key(query, 'type_id', str)
                    parameter_exists, parameter = try_get_key(query,
                                                              'parameters')
                    free_parameter_missing = not parameter_exists
                    response = await self.rooman.new_job(job_type_id,
                                                         parameter)
                elif path == '/deletejob':
                    job_id = get_key(query, 'id', str)
                    response = await self.rooman.delete_job(job_id)
                elif path == '/listjob':
                    job_type_id = query.get('type_id')
                    if not isinstance(job_type_id, str):
                        job_type_id = None
                    response = await self.rooman.list_job(job_type_id)
                elif path == '/jobaction':
                    job_id = get_key(query, 'id', str)
                    parameter_exists, parameter = try_get_key(query,
                                                              'parameters')
                    free_parameter_missing = not parameter_exists
                    response = await self.rooman.invoke_job_action(job_id,
                                                                   parameter)
                else:
                    raise errors.PathNotFoundAPIError(path)

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

            http_code = 200
            code = 'success'
            payload = response
            
        except errors.APIError as e:
            # `core` module cannot distiguish free parameter missing or
            # free parameter is just single value `None`.
            # So here, we are distinguishing these two appropriately.
            if isinstance(e, errors.FreeParameterAPIError):
                if free_parameter_missing and any(not case.path and
                        isinstance(case.error_category,
                                   core.errors.FreeParameterTypeErrorCategory)
                        for case in e.errors):
                    e = errors.ParameterMissingAPIError(['parameters'])

            http_code = e.get_http_status_code()
            code = e.get_code()
            payload = e.get_payload()

        await respond(http_code, code, payload)
