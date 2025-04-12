import sys

EXCEPTION = None
SYMBOL = None
HTTP_CONFIG = None


class FreeQuote:

    def __setitem__(self, key, value):
        self.__dict__[key] = value
        return self


def _core_const():
    def __exception():
        fq = FreeQuote()
        fq.LoadingArgs = '错误：参数错误，请调整参数后运行！ 参数:%s，允许参数：List[str,int]'
        fq.CheckRunningArgs = '错误：参数错误，运行参数中传入了非法的参数：%s, 请检查列表对象是否为空，或参数没有正确匹配'
        fq.HTTP_PROTOCOL_NOT_SUPPORTED = "错误：该协议暂不支持，请使用枚举类型：core.utils.HttpProtocolEnum"
        fq.HTTP_DOMAIN_NOT_SUPPORTED = "错误：请正确设置域名信息，当前域名：%s"
        fq.HTTP_PATH_NOT_SUPPORTED = "错误：请正确设置终端path信息，当前终端path：%s"
        fq.HTTP_JSON_DATA_NOT_SUPPORTED = "错误：请正确设置json参数信息，期望类型：dict，当前类型%s，当前值：%s"
        fq.HTTP_PARAMS_NOT_SUPPORTED = "错误：请正确设置params参数信息，期望类型：dict，当前类型%s，当前值：%s"
        fq.HTTP_HEADERS_NOT_SUPPORTED = "错误：请正确设置headers参数信息，期望类型：dict，当前类型%s，当前值：%s"
        fq.Http_Login_Failed_Exception = "错误：登录失败，原因：%s"
        fq.HTTP_Get_Task_Failed_Exception = "错误：没找到对应所属执行的测试单：%s"
        fq.TEMP_FILE_NOT_FOUND_Exception = "系统上下文管理器异常：%s 不是目录"
        fq.TEMP_File_Control_Exception = "清理失败：%s - %s"
        fq.Contxt_Exception = "系统上下文管理器未知异常：%s"
        return fq

    def __symbol():
        fq = FreeQuote()
        fq.SplitArgsSymbol = ','
        fq.ParamsStartWithSymbol = '-'
        return fq

    def __http_config():
        fq = FreeQuote()
        fq.adapters = ["http://", "https://"]
        return fq

    sys.modules[__name__].EXCEPTION = __exception()
    sys.modules[__name__].SYMBOL = __symbol()
    sys.modules[__name__].HTTP_CONFIG = __http_config()


_core_const()
