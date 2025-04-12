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


class FileException(HttpException):
    """
    文件异常
    """


class TempFileTypeException(FileException):
    """
    临时文件类型异常
    """


class TempFileNotExistException(FileException):
    """
    临时文件不存在异常
    """


class FileControlException(FileException):
    """
    文件操作异常
    """


class CustomerFuncException(ReportGenerationException):
    """
    自定义回调函数异常
    """


class ExtractException(ReportGenerationException):
    """
    解析异常
    """
