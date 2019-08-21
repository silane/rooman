class RoomanError(Exception):
    pass


class ActionIDNotFoundError(RoomanError):
    def __init__(self, action_id):
        super().__init__(action_id)
        self.target = action_id


class JobTypeIDNotFoundError(RoomanError):
    def __init__(self, job_type_id):
        super().__init__(job_type_id)
        self.target = job_type_id


class JobIDNotFoundError(RoomanError):
    def __init__(self, job_id):
        super().__init__(job_id)
        self.target = job_id


class FreeParameterError(RoomanError):
    def __init__(self, error_cases):
        super().__init__(error_cases)
        self.errors = error_cases


class NewJobFreeParameterError(FreeParameterError):
    pass


class JobActionFreeParameterError(FreeParameterError):
    pass


class FreeParameterErrorCase:
    def __init__(self, path, value, error_category):
        self.path = path
        self.value = value
        self.error_category = error_category


class FreeParameterErrorCategory:
    def get_code(self):
        raise NotImplementedError()

    def get_params(self):
        return None


class FreeParameterTypeErrorCategory(FreeParameterErrorCategory):
    def __init__(self, correct_type):
        self.correct_type = correct_type

    def get_code(self):
        return 'type'

    def get_params(self):
        return {'correct_type': str(self.correct_type)}


class FreeParameterValueErrorCategory(FreeParameterErrorCategory):
    def get_code(self):
        return 'value'


class FreeParameterKeyErrorCategory(FreeParameterErrorCategory):
    def __init__(self, key):
        self.key = key

    def get_code(self):
        return 'key'

    def get_params(self):
        return {'key': self.key}


def single_case_free_parameter_error(path, value, error_category):
    """
    Just a handy shourtcut function.
    """
    return FreeParameterError([FreeParameterErrorCase(
        path, value, error_category)])


def free_parameter_type_error(path, value, correct_type):
    return single_case_free_parameter_error(
        path, value, FreeParameterTypeErrorCategory(correct_type))


def free_parameter_value_error(path, value):
    return single_case_free_parameter_error(
        path, value, FreeParameterValueErrorCategory())


def free_parameter_key_error(path, value, key):
    return single_case_free_parameter_error(
        path, value, FreeParameterKeyErrorCategory(key))


class RuntimeRoomanError(RoomanError):
    def __init__(self, detail=None):
        self.detail = detail