import os
import struct
from typing import Tuple

HEX_PATTERN = {
    "public_front": """
d0 cf 11 e0 a1 b1 1a e1  06 09 02 00 00 00 00 00
c0 00 00 00 00 00 00 46  3e 00 03 00 fe ff 09 00
06 00 00 00 00 00 00 00  00 00 00 00 2c 00 00 00
bf 15 00 00 00 00 00 00  00 10 00 00 be 15 00 00
01 00 00 00 fe ff ff ff  00 00 00 00 c4 15 00 00
5c 01 00 00 5d 01 00 00  ff ff ff ff ff ff ff ff
""",
    "file_front": "%s d4 04 00 02 00",
    "fixed_file_path_end": "00 00 00 03 00 %s 00 00 00",
    "end": "00 b0 d3 04 00"
}


def get_file_front(path) -> Tuple[str, str]:
    return build_ole10native_bin(path)


def get_fixed_file_path_end(path):
    return HEX_PATTERN["fixed_file_path_end"] % (str(hex(len(path.encode("gbk")) + 1))[2:],)


def write_bin_data(file_origin_path, original_data, output_file_path):
    header_bytes = bytes.fromhex(
        " ".join(
            line.split("|")[0].strip()  # 提取左边十六进制部分
            for line in HEX_PATTERN["public_front"].strip().split("\n")
        )
    )

    padding_length = 512 - len(header_bytes)  # 416字节
    full_header = header_bytes + b"\xff" * padding_length
    file_front_string, fixed_file_path_end_string = get_file_front(file_origin_path)
    fixed_bytes = bytes.fromhex(file_front_string)
    full_header += fixed_bytes  # 现在总长度 = 512 + 6 = 518字节

    filename = os.path.basename(file_origin_path)
    filename_bytes = filename.encode("gbk") + b"\x00"
    full_header += filename_bytes
    file_origin_path_bytes = file_origin_path.encode("gbk")

    full_header += file_origin_path_bytes
    fixed_file_end_bytes = bytes.fromhex(get_fixed_file_path_end(file_origin_path))
    full_header += fixed_file_end_bytes
    full_header += file_origin_path_bytes

    end_bytes = bytes.fromhex(fixed_file_path_end_string)
    full_header += end_bytes

    with open("/Users/sheldon/Documents/GithubProject/Observer-Toolbox/core/tooller/static/base_end.bin", "rb") as f:
        end_data = f.read()

    # 写入新文件（头部 + 原始内容）
    with open(output_file_path, "wb") as f:
        f.write(full_header)  # 写入自定义头部
        f.write(original_data)  # 追加原始内容
        f.write(end_data)


def build_ole10native_bin(
        payload_path: str,
        ansi_encoding: str = "gbk"
) -> Tuple[str, str]:
    def split_path(full_path: str) -> Tuple[str, str]:
        """
        将完整路径分解为文件名（不含扩展名）和路径部分（以 / 结尾）

        参数:
            full_path (str): 完整的文件路径

        返回:
            Tuple[str, str]: (文件名不含扩展名, 路径部分)
        """
        dirname = os.path.dirname(full_path)
        basename = os.path.basename(full_path)
        filename, _ = os.path.splitext(basename)
        return filename, dirname + "/"

    filename, dirname = split_path(payload_path)
    with open(payload_path, "rb") as f:
        payload = f.read()

    flags1 = struct.pack("<H", 0x0002)

    counting = len(filename.encode(ansi_encoding)) * 3 + len(dirname) * 3
    ansi_label = filename.encode(ansi_encoding, errors="ignore")
    ansi_path = dirname.encode(ansi_encoding, errors="ignore")
    payload_bytes_string = "00 " + " ".join(f"{b:02x}" for b in struct.pack("<I", len(payload))[:6])
    body = flags1 + ansi_label + ansi_path + payload
    header = struct.pack("<I", len(payload) + counting)
    header_bytes_string = " ".join(f"{b:02x}" for b in header[:6]) + " 02 00"
    return header_bytes_string, payload_bytes_string
