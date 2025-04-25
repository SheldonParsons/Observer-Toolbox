import os
import shutil
import struct
from pathlib import Path
from typing import Union, List
from urllib.parse import urlparse

from olefile import OleFileIO

from core.tooller.async_server import DownloadServerType, AsyncServerController

size_refer_list = [50, 100, 200, 300, 400, 500, 600, 800, 1000, 2000, 3000, 4000, 5000, 7000, 9000, 11000, 22000,
                   33000, 44000, 55000]

REMOTE_OSS_SERVER = "https://obersertoolbox-testreport.oss-cn-shenzhen.aliyuncs.com/ole_object_bin_templates/"


def select_best_template(template_dir: Path, payload_len: int) -> Union[Path, None]:
    target_size = min(filter(lambda size: size >= (payload_len / 1024), size_refer_list))
    temp_file_path = template_dir / f"oleObject{target_size}.bin"
    if os.path.exists(temp_file_path):
        return temp_file_path


def generate_bin_file(prepare_save_file_path: List[str] = None, save_dir: Path = None):
    target_size_set = set()
    for path in prepare_save_file_path:
        if isinstance(path, str) is False:
            continue
        data_size = os.path.getsize(path)
        target_size = min(filter(lambda size: size >= (data_size / 1024), size_refer_list))
        target_size_set.add(target_size)
    get_remote_url_list = []
    for target_size in target_size_set:
        os.makedirs(save_dir, exist_ok=True)
        file_name = f"oleObject{target_size}.bin"
        temp_file_path = save_dir / file_name
        if os.path.exists(temp_file_path) is False:
            get_remote_url_list.append(REMOTE_OSS_SERVER + file_name)
    if len(get_remote_url_list) > 0:
        def get_filename_func(url: str, *args) -> str:
            path = urlparse(url).path
            return os.path.basename(path)

        AsyncServerController().generator_files(DownloadServerType.CUSTOM_REQUESTS,
                                                customer_extract_func=get_filename_func,
                                                request_list=get_remote_url_list, customer_dir=save_dir,
                                                force_cover_file_name=True)


def build_ole10native_stream(data: bytes, filename: str) -> bytes:
    # 按 oletools OLENativeStream 结构逆向构造
    native_size = len(data)
    parts = [
        struct.pack("<I", native_size),  # NativeDataSize
        struct.pack("<H", 0),  # unknown_short
        filename.encode('gbk') + b'\x00',  # filename + terminator
        b'\x00',  # src_path empty + terminator
        struct.pack("<II", 0, 0),  # two FILETIME 占位
        b'\x00',  # temp_path terminator
        struct.pack("<I", native_size),  # actual_size
        data  # NativeData
    ]
    return b"".join(parts)


def create_bin_with_padding(template_dir: Path, output_path: Path, payload: bytes, name: str):
    new_stream = build_ole10native_stream(payload, name)
    template_path = select_best_template(template_dir, len(new_stream))
    shutil.copy(template_path, output_path)
    # 打开模板 .bin（含空白流）
    ole = OleFileIO(output_path, write_mode=True)
    orig = ole.openstream("Ole10Native").read()
    new_stream += b'\x00' * (len(orig) - len(new_stream))
    ole.write_stream("Ole10Native", new_stream)  # :contentReference[oaicite:7]{index=7}
    ole.close()
