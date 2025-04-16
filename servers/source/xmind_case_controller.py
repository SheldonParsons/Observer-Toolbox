# -*-coding: Utf-8 -*-
# @File : xmind_case_result .py
# author: A80723
# Time：2025/3/19 
# Description：
import os,zipfile
from xmindparser import xmind_to_dict
from core.root import  get_base_dir


def xmind_dict(filename):
    dict_data = xmind_to_dict(filename)
    return dict_data

def Get_tree_data(testdata,case_data,indexnum=0,treedata=[],mark=None):#递归把树状dict的值单独取出来
    marks=mark
    task_type=''
    if isinstance(testdata,list):
        for i in testdata:
            Get_tree_data(i, case_data,indexnum=indexnum,treedata=treedata,mark=marks)
    if isinstance(testdata, dict):#为字典时是最外面一层，取模块
        if indexnum>=len(treedata):
            treedata.append(testdata['title'])
        else:
            #小于长度的时候把当前长度后面的元素都删除掉
            del treedata[indexnum:len(treedata)]
            marks = None#清除后先默认把优先级改为3
            treedata.append(testdata['title'])
        if "makers" in testdata.keys():
            marksvalue=testdata['makers']
            # 查找包含"priority"的元素
            priority_items = [item for item in marksvalue if item.startswith('priority')]
            task_items = [item for item in marksvalue if item.startswith('task')]
            if priority_items:
                marks=priority_items[0].split('-')[1]
            if task_items:
                task_type = task_items[0].split('-')[1]
        if "topics" in testdata.keys():
            index=indexnum+1
            Get_tree_data(testdata['topics'],case_data,indexnum=index,treedata=treedata,mark=marks)
        else:#最后一层
            if treedata[-1] != "通过" and task_type=='done':
                treedata.append('通过')
            else:
                treedata.append('未执行')
            treedata.append(marks)
            case_data.extend([treedata])  # 新开个内存存储，不会被del删除掉

# 统计用例执行情况
def statistics_case(case_data):
    new_addition_data=len(case_data) # 新增用例
    passed_count = sum(1 for sublist in case_data if sublist[-2] == "通过") # 获取测试通过的个数
    failed_count = sum(1 for sublist in case_data if sublist[-2] == "失败") # 获取测试失败的个数
    unexecuted_count = sum(1 for sublist in case_data if sublist[-2] == "未执行")  # 获取测试失败的个数
    return new_addition_data, passed_count, failed_count, unexecuted_count



def sum_statistics_data(directory,zipname):
    '''输出格式:本次版本设计了 1210 条用例，通过了 1210个用例，失败了0个用例，通过率 100%'''
    # directory=[r"F:\Gree\格力钱包\2025\0330\调账昵称.xmind"]#测试用
    dir = get_base_dir()
    path = dir / zipname
    print(f"侍处理文件地址{directory}")
    new_addition_data=0
    passed_count=0
    failed_count=0
    unexecuted_count=0
    case_list=[]
    for file in directory:
        # 输出文件的完整路径
        case_data = []
        file_path = file
        print(file_path)
        testdata=xmind_dict(file_path)
        for case in testdata:
            Get_tree_data(case['topic'],case_data)
        statistics_data=statistics_case(case_data)
        new_addition_data+=statistics_data[0]
        passed_count += statistics_data[1]
        failed_count += statistics_data[2]
        unexecuted_count += statistics_data[3]
        case_list.append(file_path)
    pass_rate = "{:.2%}".format(passed_count / new_addition_data)
    fail_rate = "{:.2%}".format(failed_count / new_addition_data)
    print(f'本次新增用例数{new_addition_data}')
    print(f'本次通过用例数{passed_count}')
    print(f'本次失败用例数{failed_count}')
    print(f'本次未执行用例数{unexecuted_count}')
    case_result=f'本次版本设计了 {new_addition_data} 条用例，通过了 {passed_count}个用例，失败了{failed_count}个用例，通过率 {pass_rate}'
    #压缩xmind
    zip_xmindpath=path
    zip_path=zip_xmindfile(case_list,zip_xmindpath)
    return case_result, zip_path

def zip_xmindfile(case_list,output_path):
    '''
        打包xmind文件
    '''
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加多个文件
        for file in case_list:
            zipf.write(file,arcname=os.path.basename(file))
    return output_path

def test_001():
    directory=[r"F:\Gree\格力钱包\2025\0330\调账昵称.xmind"]
    zip_path="F:\\Gree\\github\\TestReport\\core\\temp/测试报告.zip"
    result=sum_statistics_data(directory,zip_path)
    print(result)
if __name__ == '__main__':
    test_001()