import os
import re
from typing import List

from openpyxl.styles import Font, Alignment
from openpyxl.workbook import Workbook

from core.root import get_base_dir
from servers.source.zendao_file_info import bug_sheet_title, bug_fields


class BugFileStream:
    class _ColumnBaseInfo:
        def __init__(self, header_name, field_name, default_value):
            self.header_name = header_name
            self.field_name = field_name
            self.default_value = default_value

    def __init__(self, file_name):
        self.work_book = Workbook()
        self.work_sheet = self.work_book.active
        self.work_sheet.title = bug_sheet_title
        self.dir = get_base_dir()
        self.path = self.dir / file_name
        self.headers = [self._ColumnBaseInfo(*header) for header in bug_fields]

    def dir_exist_check(self):
        if self.dir and not os.path.exists(self.dir):
            os.makedirs(self.dir, exist_ok=True)

    def __enter__(self):
        self.dir_exist_check()
        return self.work_book, self.work_sheet, self.headers

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.work_book.save(self.path)
        self.work_book.close()


def calculate_char_width(char):
    # 中文要宽一些
    return 2 if ord(char) > 255 else 1


def get_column_width(column):
    # 获取最大列宽
    width_list = []
    for cell in column:
        if cell.value:
            cell_width = sum(calculate_char_width(c) for c in str(cell.value).split('\n')[0])
            width_list.append(cell_width)
    return max(*width_list) + 10


def html_to_text(html: str):
    # 清除html标记
    text = str(html).replace('<br />', '\n').replace('<br>', '\n')
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ')
    return re.sub(r'\n{2,}', '\n', text).strip()


def process_value(value, h: BugFileStream._ColumnBaseInfo):
    # 特殊处理
    if h.field_name in ["openedBy", "assignedTo"]:
        value = value["realname"]
    if h.field_name in ["steps"]:
        value = html_to_text(value)
    if isinstance(value, str) is False:
        value = str(value)
    return value


def generate_bug_file(file_name, row_data: List[dict]) -> None:
    with BugFileStream(file_name) as (work_book, work_sheet, headers):
        # 添加表头
        work_sheet.append([h.header_name for h in headers])
        # 给表头设定特殊样式
        work_sheet.row_dimensions[1].alignment = Alignment(horizontal='center', vertical='center')
        work_sheet.row_dimensions[1].font = Font(bold=True)
        # 模式匹配：为每行添加数据
        for col in row_data:
            work_sheet.append([(_ := lambda v: h.default_value if v in (None, "", []) else
            "\n".join(map(str, v)) if isinstance(v, list) else
            process_value(v, h).strip())(col.get(h.field_name))
                               for h in headers])
        # 动态设置列宽
        for column in work_sheet.columns:
            width = get_column_width(column)
            work_sheet.column_dimensions[column[0].column_letter].width = width
