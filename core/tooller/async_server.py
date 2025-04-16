from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import aiohttp
import asyncio
import aiofiles
import os
import re
from typing import Union, List, Optional, Callable
from urllib.parse import urlparse, parse_qs, unquote
from asyncio import Semaphore
from pathlib import Path
from core.generator import report_exception

from core.root import get_base_dir

DEFAULT_CHUNK_SIZE = 1024 * 16
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=60)
MAX_CONCURRENT = 10
VALID_SCHEMES = ('http', 'https')


class DownloadServerType(str, Enum):
    K_DOCS = "kdocs_files_path"


class AsyncServerController:
    def __init__(self):
        self.save_dir = Path(get_base_dir())
        self.semaphore = Semaphore(MAX_CONCURRENT)
        self.url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        self.customer_extract_func = None
        self.second_path = Path("")

    def generator_files(self, server_type: DownloadServerType = DownloadServerType.K_DOCS,
                        customer_extract_func: Callable[[str, ...], Union[str, None]] = None,
                        path: Union[Path, str] = Path("")) -> \
            tuple[BaseException | str]:
        """
        下载并生成文件任务
        :param server_type: 需要下载的服务类型，当前仅提供kdocs
        :param customer_extract_func: 自定义URL中解析文件名的回调函数
        :param path: 以core/temp为根路径下的二级路径
            e.g.:(1) "abc/edf" 以【/】分割路径，将会自动创建abc/edf，最终保存路径：core/temp/abc/def
            e.g.:(2) pathlib.Path("abc/edf")，将Path对象与根路径结合，将会自动创建abc/edf，最终保存路径：core/temp/abc/def
        :return: 下载文件保存的路径以及下载任务异常集成的列表
        """
        self.second_path = path
        self.customer_extract_func = customer_extract_func
        from core.generator import GlobalData
        urls_data = GlobalData.system_parameters.__dict__[server_type.value]
        urls_list = self._process_http_urls(urls_data)
        return asyncio.run(self._run(urls_list))

    async def _run(self, urls: List[str]):
        """执行异步下载任务"""
        async with aiohttp.ClientSession(
                timeout=DEFAULT_TIMEOUT,
                connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            tasks = [self._download_task(session, url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)

    async def _download_task(self, session: aiohttp.ClientSession, url: str):
        """单个下载任务协程"""
        async with self.semaphore:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    filename = self._extract_filename(url) or self._fallback_filename(url)
                    save_path = await self._get_unique_path(filename)
                    await self._stream_to_file(response, save_path)
                    return str(save_path)
            except aiohttp.ClientError as e:
                raise report_exception.HttpException(f"{response.status or None}：{url}]: {str(e)}")
            except Exception as e:
                raise report_exception.HttpException(f"未知错误 [{url}]: {str(e)}")

    def _extract_filename(self, url: str) -> Optional[str]:
        # 自定义解析
        if self.customer_extract_func is not None:
            try:
                return self.customer_extract_func(url)
            except Exception as e:
                raise report_exception.CustomerFuncException(
                    f"自定义函数：{self.customer_extract_func}，解析url：{url}，错误：{e}")

        # 默认解析
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            content_disp = params.get("response-content-disposition", [""])[0]

            if filename_part := next((
                    p.split("=", 1)[1]
                    for p in content_disp.split(";")
                    if p.strip().startswith("filename*=")
            ), None):
                if "utf-8''" in filename_part:
                    return unquote(filename_part.split("utf-8''")[1])

            if filename_part := next((
                    p.split("=", 1)[1].strip('"')
                    for p in content_disp.split(";")
                    if p.strip().startswith("filename=")
            ), None):
                return unquote(filename_part)

        except Exception as e:
            raise report_exception.FileException(f"文件名解析失败 [{url}]: {str(e)}")
        return None

    async def _get_unique_path(self, filename: str) -> Path:
        """生成唯一路径并原子性预留文件（协程安全）"""
        second_path = Path(self.second_path) if self.second_path else Path()

        if second_path.is_absolute():
            second_path = Path(*second_path.parts[1:])  # 移除绝对路径的根目录

        base_dir = self.save_dir / second_path
        base_name, ext = os.path.splitext(filename)

        counter = 0
        while True:
            new_name = f"{base_name}_{counter}{ext}" if counter > 0 else filename
            path = base_dir / new_name

            try:
                loop = asyncio.get_running_loop()
                io_executor = ThreadPoolExecutor(max_workers=4)
                await loop.run_in_executor(io_executor, lambda: path.parent.mkdir(parents=True, exist_ok=True))

                async with aiofiles.open(path, "xb") as f:  # 'x' 表示独占创建模式
                    pass

                return path

            except FileExistsError:
                counter += 1

    def _process_http_urls(self, urls_data: Union[str, List[str]]) -> List[str]:
        """处理并验证URL输入"""
        if isinstance(urls_data, str):
            return self._process_file_input(urls_data)
        elif isinstance(urls_data, list):
            return self._validate_urls(urls_data)
        raise TypeError("输入类型必须是字符串路径或字符串列表")

    def _validate_urls(self, urls: List[str]) -> List[str]:
        """验证URL合法性"""
        valid_urls = []
        for url in urls:
            if self._is_valid_url(url):
                valid_urls.append(url)
            else:
                raise report_exception.ExtractException(f"无效URL被过滤: {url}")
        return valid_urls

    def _is_valid_url(self, url: str) -> bool:
        """URL格式验证"""
        if not url.startswith(('http://', 'https://')):
            return False
        try:
            result = urlparse(url)
            return all([
                result.scheme in VALID_SCHEMES,
                result.netloc,
                self.url_pattern.match(url)
            ])
        except ValueError:
            return False

    @staticmethod
    async def _stream_to_file(response: aiohttp.ClientResponse, save_path: Path):
        """流式写入文件"""
        async with aiofiles.open(save_path, "wb") as f:
            async for chunk in response.content.iter_chunked(DEFAULT_CHUNK_SIZE):
                await f.write(chunk)  # type: ignore

    @staticmethod
    def _fallback_filename(url: str) -> str:
        """备用文件名生成策略"""
        parsed = urlparse(url)
        path = Path(parsed.path)
        if path.suffix:
            return f"file_{hash(url)}{path.suffix}"
        return f"file_{hash(url)}"

    @staticmethod
    def _process_file_input(file_path: str) -> List[str]:
        path = Path(file_path)
        if not path.exists():
            raise report_exception.FileException(f"文件不存在: {file_path}")
        if not path.is_file():
            raise report_exception.FileException(f"路径不是文件: {file_path}")

        try:
            return [line.strip() for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        except UnicodeDecodeError:
            raise report_exception.FileException("仅支持 UTF-8 编码的文本文件")
