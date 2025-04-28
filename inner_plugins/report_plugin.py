from typing import Union

from docx import Document

from core.deco import inner_plugin
from core.base import T, RunnerResult, Data
from core.generator import ServicePlugin
from core.tooller.insert_ole_to_docx import insert_files_to_docx


@inner_plugin
class ReportPlugin(ServicePlugin):
    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        print("run inner ReportPlugin")
        return "result inner ReportPlugin"

    def get_notify(self, data: Data):
        result: RunnerResult = data.result
        result_data = result.get_data()
        if result.source_name == 'ExcelSummaryPlugin':
            test1_file_path = result_data.xmind_file_list[0:3]
            test2_file_path = result_data.xmind_file_list[3:5]
            doc = Document("/Users/sheldon/Documents/GithubProject/Observer-Toolbox/xmindcase/output_real.docx")
            insert_mapping = {
                "{file.zip}": test1_file_path,
                "{bugs.xlsx}": test2_file_path
            }
            insert_files_to_docx(doc, insert_mapping)
            print(f"result_data.summary_data:{result_data.summary_data}")
            print(f"result_data.pic_list:{result_data.pic_list}")
