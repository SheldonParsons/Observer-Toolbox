class ReportGenerationException(BaseException):

    def __init__(self, message):
        self.message = message


class HttpException(ReportGenerationException):
    pass


class HttpConfigException(HttpException):
    """
    Http 参数错误
    """

class HttpResponseException(HttpException):
    """
    Http 响应错误
    """
