import os
import re
import shutil
import struct
from pathlib import Path
from typing import Union

from olefile import OleFileIO


def select_best_template(template_dir: Path, payload_len: int) -> Union[str, None]:
    size_list = []
    for filename in os.listdir(template_dir):
        match = re.search(r'oleObject(\d+)\.bin', filename)
        if match:
            size_kb = int(match.group(1))
            size_list.append(size_kb)
    size_list.sort()
    for item in size_list:
        if item >= (payload_len / 1024):
            return os.path.join(template_dir, f"oleObject{item}.bin")
    return None


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
    print(f"template_path:{template_path}")
    shutil.copy(template_path, output_path)
    # 打开模板 .bin（含空白流）
    print(f"output_path:{output_path}")
    ole = OleFileIO(output_path, write_mode=True)
    orig = ole.openstream("Ole10Native").read()
    new_stream += b'\x00' * (len(orig) - len(new_stream))
    ole.write_stream("Ole10Native", new_stream)  # :contentReference[oaicite:7]{index=7}
    ole.close()
