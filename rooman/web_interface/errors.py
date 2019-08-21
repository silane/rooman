class APIError(Exception):
    def get_http_status_code(self):
        raise NotImplementedError()

    def get_code(self):
        raise NotImplementedError()

    def get_payload(self):
        return None


class ActionIDNotFoundAPIError(APIError):
    def __init__(self, action_id):
        self.action_id = action_id
        super().__init__(action_id)

    def get_http_status_code(self):
        return 400

    def get_code(self):
        return 'actionid_notfound'

    def get_payload(self):
        return {'target': self.action_id}


class JobTypeIDNotFoundAPIError(APIError):
    def __init__(self, job_type_id):
        self.job_type_id = job_type_id
        super().__init__(job_type_id)

    def get_http_status_code(self):
        return 400

    def get_code(self):
        return 'jobtypeid_notfound'

    def get_payload(self):
        return {'target': self.job_type_id}


class JobIDNotFoundAPIError(APIError):
    def __init__(self, job_id):
        self.job_id = job_id
        super().__init__(job_id)

    def get_http_status_code(self):
        return 400

    def get_code(self):
        return 'jobid_notfound'

    def get_payload(self):
        return {'target': self.job_id}


class PathNotFoundAPIError(APIError):
    def __init__(self, path):
        self.path = path
        super().__init__(path)

    def get_http_status_code(self):
        return 404

    def get_code(self):
        return 'path_notfound'

    def get_payload(self):
        return {'target': self.path}


class ParameterMissingAPIError(APIError):
    def __init__(self, missing_parameters):
        self.missing_parameters = list(missing_parameters)
        super().__init__(missing_parameters)

    def get_http_status_code(self):
        return 400

    def get_code(self):
        return 'parameter_missing'

    def get_payload(self):
        return {'missing_parameters': self.missing_parameters}


class ParameterFormatAPIError(APIError):
     def __init__(self, format_error_parameters):
         super().__init__(format_error_parameters)
         self.format_error_parameters = format_error_parameters

     def get_http_status_code(self):
         return 400

     def get_code(self):
         return 'invalid_parameter_format'

     def get_payload(self):
         return {'format_error_parameters': self.format_error_parameters}


class FreeParameterAPIError(APIError):
    def __init__(self, error_cases):
        super().__init__(error_cases)
        self.errors = error_cases

    def get_http_status_code(self):
        return 400

    def get_payload(self):
        return [{'path': case.path, 'category': {
            'code': case.error_category.get_code(),
            'params': case.error_category.get_params(),
        }} for case in self.errors]


class NewJobFreeParameterAPIError(FreeParameterAPIError):
    def get_code(self):
        return 'invalid_new_job_parameter'


class JobActionFreeParameterAPIError(FreeParameterAPIError):
    def get_code(self):
        return 'invalid_job_action_parameter'


class RuntimeAPIError(APIError):
    def __init__(self, detail=None):
        self.detail = detail

    def get_http_status_code(self):
        return 500

    def get_code(self):
        return 'internalserver_error'

    def get_payload(self):
        return self.detail
