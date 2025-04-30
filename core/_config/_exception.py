class ObserverToolboxException(BaseException):

    def __init__(self, message):
        self.message = message


class SystemParameterException(ObserverToolboxException):
    """
    系统参数错误
    """


class HttpException(ObserverToolboxException):
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


class CustomerFuncException(ObserverToolboxException):
    """
    自定义回调函数异常
    """


class ExtractException(ObserverToolboxException):
    """
    解析异常
    """


class ModuleException(ObserverToolboxException):
    """
    模块异常
    """


class ModuleNotFoundException(ModuleException):
    """
    模块不存在
    """
