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
        print("*" * 10 + "inner ReportPlugin Monitor" + "*" * 10)
        print(f"method_name: {data.method_name}")
        print(f"obj:{data.obj}")
        print(f"data:{data.result}")
        result: RunnerResult = data.result
        print(f"source_name:{result.source_name}")
        print(f"source_type:{result.source_type}")
        print(f"get_data():{result.get_data()}")
        rusult_data = result.get_data()
        if result.source_name == 'ZenDaoServer' and data.method_name == "run":
            print(f"rusult_data.case_result:{rusult_data.temp_path}")
            test1_file_path = rusult_data.temp_path[0:5]
            test2_file_path = rusult_data.temp_path[5:10]
            doc = Document("/Users/sheldon/Documents/GithubProject/Observer-Toolbox/xmindcase/output_real.docx")
            insert_mapping = {
                "{file.zip}": test1_file_path,
                "{bugs.xlsx}": test2_file_path
            }
            insert_files_to_docx(doc, insert_mapping)
