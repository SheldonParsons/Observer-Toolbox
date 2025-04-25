import os
import zipfile
from pathlib import Path
from shutil import rmtree, copyfile
from tempfile import mkdtemp
from typing import List, Union
from uuid import uuid4
from lxml.etree import parse, Element, SubElement, tostring, register_namespace
import lxml

from docx import Document

from core.root import BASE_DIR, get_base_dir
from core.tooller._gen_pic import generator_icon_picture
from core.tooller._gen_bin_file import create_bin_with_padding, generate_bin_file

ICON_CONFIG = {
    '.xlsx': Path(BASE_DIR) / 'core' / 'tooller' / 'static' / 'icns' / 'xlsx.icns',
    '.docx': Path(BASE_DIR) / 'core' / 'tooller' / 'static' / 'icns' / 'docx.icns',
    '.doc': Path(BASE_DIR) / 'core' / 'tooller' / 'static' / 'icns' / 'docx.icns',
    '.zip': Path(BASE_DIR) / 'core' / 'tooller' / 'static' / 'icns' / 'zip.icns',
    '.xmind': Path(BASE_DIR) / 'core' / 'tooller' / 'static' / 'icns' / 'xmind.icns',
    '.pdf': Path(BASE_DIR) / 'core' / 'tooller' / 'static' / 'icns' / 'pdf.icns'
}

ICON_DEFAULT_CONFIG = Path(BASE_DIR) / 'core' / 'tooller' / 'static' / 'icns' / 'default.icns'

DEFAULT_FONT_PATH = Path(BASE_DIR) / 'core' / 'tooller' / 'static' / 'fonts' / 'Arial Unicode.ttf'

OLE_TEMPLATE_DIR = Path(BASE_DIR) / 'core' / 'tooller' / 'static' / 'templates'

NAMESPACE = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'o': 'urn:schemas-microsoft-com:office:office',
    'v': 'urn:schemas-microsoft-com:vml'
}
for key, value in NAMESPACE.items():
    register_namespace(key, value)
# Temp
TEMPLATE_DOCX_FILE_NAME = 'template.docx'
# 核心文件和目录
DOCUMENT_XML = 'word/document.xml'
DOCUMENT_XML_RELS = 'word/_rels/document.xml.rels'
EMBEDDINGS_DIR = 'word/embeddings'
MEDIA_DIR = 'word/media'
# Type
FILE_TYPE_REFERENCE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject'
IMAGE_TYPE_REFERENCE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'

# 插入文件最多一行显示个数
FILE_SHOW_SPLIT = 3


class SearchElement:

    def __init__(self, target, index):
        self.target: lxml.etree._Element = target
        self.index = index


class DocxOleEmbedderController:

    def __init__(self, origin_docx: Document, insert_mapping: dict[str, List] = None):
        self.insert_mapping = insert_mapping
        self.origin_docx = origin_docx
        self.temp_dir: Union[str, None, Path] = None
        self.shape_index = 24
        self.search_parent_object_mapping = {}
        self.save_file_count = 0

    def __enter__(self):
        self.temp_dir = Path(mkdtemp())
        # 前置准备工作
        _temp_file_path = Path(self.temp_dir) / TEMPLATE_DOCX_FILE_NAME
        self.origin_docx.save(_temp_file_path)
        # 解压 DOCX 文件
        with zipfile.ZipFile(_temp_file_path, 'a') as docx_zip:
            docx_zip.extractall(self.temp_dir)
        self.document_xml = self.temp_dir / DOCUMENT_XML
        self.rels_xml = self.temp_dir / DOCUMENT_XML_RELS
        self.embeddings_dir = self.temp_dir / EMBEDDINGS_DIR
        self.media_dir = self.temp_dir / MEDIA_DIR
        # 解析文件成element对象
        self.doc_tree: lxml.etree._ElementTree = self._parse_xml(self.document_xml)
        self.rels_tree: lxml.etree._ElementTree = self._parse_xml(self.rels_xml)
        self.relationship_count = len(self.rels_tree.getroot())
        return self

    def action(self):
        generate_bin_file([item for sublist in self.insert_mapping.values() for item in sublist], OLE_TEMPLATE_DIR)
        for search_string, file_path_list in self.insert_mapping.items():
            self.save_file_count = 0
            is_set_and_remove = self._set_and_remove_tag_element(search_string)
            if is_set_and_remove:
                new_r_element_obj_list = []
                new_p_element_obj_list = []
                # 整体添加relationship、embedded_file
                for embedded_data, file_path in self._get_file_data(file_path_list):
                    if isinstance(file_path, str) is False:
                        continue
                    ole_id = self._get_ole_id()
                    rel_id = self.get_target_id()
                    self._add_relationship(FILE_TYPE_REFERENCE, f'embeddings/{ole_id}.bin')
                    self._save_embedded_file(file_path, embedded_data, ole_id)
                    # 更新document.xml
                    new_element_obj = self._generator_single_file_obj(rel_id, os.path.basename(file_path))
                    new_r_element_obj_list.append(new_element_obj)
                # 重排整合
                matrix_element = self.chunk_list(new_r_element_obj_list, FILE_SHOW_SPLIT)
                for element_list in matrix_element:
                    new_p = Element('{%s}p' % NAMESPACE['w'])
                    list(new_p.append(r_element) for r_element in element_list)
                    new_p_element_obj_list.append(new_p)
                _search_element: SearchElement = self.search_parent_object_mapping[search_string]
                origin_index = _search_element.index
                # 插入
                for idx, new_element in enumerate(new_p_element_obj_list):
                    _search_element.target.insert(origin_index + idx + 1, new_element)
            self._save_xml(self.doc_tree, self.document_xml)
        return self.save()

    @staticmethod
    def chunk_list(lst, size):
        return [lst[i:i + size] for i in range(0, len(lst), size)]

    def _generator_single_file_obj(self, rel_id, filename):
        self.shape_index += 1
        obj = Element('{%s}object' % NAMESPACE['w'], {
            '{%s}dxaOrig' % NAMESPACE['w']: '1440',
            '{%s}dyaOrig' % NAMESPACE['w']: '1440'
        })

        shape = SubElement(obj, '{%s}shape' % NAMESPACE['v'], {
            'id': "_x0000_i10" + str(self.shape_index),
            'type': '#_x0000_t75',
            'style': 'width:50pt;height:15pt',
            '{%s}ole' % NAMESPACE['o']: ''
        })

        # 创建 OLEObject 元素
        ole_obj = SubElement(obj, '{%s}OLEObject' % NAMESPACE['o'], {
            'Type': 'Embed',
            'ProgID': self._get_progid(filename),
            'ShapeID': "_x0000_i10" + str(self.shape_index),
            'DrawAspect': 'Icon',
            'ObjectID': f'_{uuid4().hex}',
            '{%s}id' % NAMESPACE['r']: rel_id,  # 正确关联 OLE 对象关系
            'DisplayName': filename,
        })

        icon_rel_id = self._embed_icon_with_relationship(filename)
        # 添加图标显示控制
        icon_pict = SubElement(ole_obj, '{%s}IconPict' % NAMESPACE['o'])
        SubElement(icon_pict, '{%s}pict' % NAMESPACE['v'], {
            '{%s}id' % NAMESPACE['r']: icon_rel_id  # 关联图标关系
        })

        # 设置图标尺寸
        ole_obj.set('{%s}IconWidth' % NAMESPACE['o'], '320000')
        ole_obj.set('{%s}IconHeight' % NAMESPACE['o'], '320000')

        # 创建 imagedata 用于 OLE 对象
        SubElement(shape, '{%s}imagedata' % NAMESPACE['v'], {
            '{%s}id' % NAMESPACE['r']: icon_rel_id,  # 关联 OLE 对象关系
            '{%s}title' % NAMESPACE['o']: ''
        })
        new_r = Element('{%s}r' % NAMESPACE['w'])
        # new_r = SubElement(new_p, '{%s}r' % NAMESPACE['w'])
        new_r.append(obj)

        return new_r

    def _save_embedded_file(self, file_path, file_content, ole_id):
        os.makedirs(self.embeddings_dir, exist_ok=True)
        if not file_path.lower().endswith(('.doc', '.docx')):
            create_bin_with_padding(Path(BASE_DIR) / "core" / "tooller" / "static" / "templates",
                                    self.embeddings_dir / f'{ole_id}.bin', file_content, os.path.basename(file_path))
        else:
            with open(os.path.join(self.embeddings_dir, f'{ole_id}.bin'), 'wb') as f:
                f.write(file_content)

    def _add_relationship(self, file_type, target_path):
        file_id = self.get_target_id()
        attrib = {
            'Id': file_id,
            'Type': file_type,
            'Target': target_path
        }
        SubElement(self.rels_tree.getroot(), 'Relationship', attrib)
        self._save_xml(self.rels_tree, self.rels_xml)
        self.relationship_count += 1
        return file_id

    def _set_and_remove_tag_element(self, search_string: str):
        root = self.doc_tree.getroot()
        for p_elem in root.iterfind('.//w:p', namespaces=NAMESPACE):
            for r_elem in p_elem.iterfind('.//w:r', namespaces=NAMESPACE):
                t_elem = r_elem.find('.//w:t', namespaces=NAMESPACE)
                if t_elem is not None and search_string in t_elem.text:
                    # 记录父元素和位置
                    _search_element = SearchElement(p_elem.getparent(), list(p_elem.getparent()).index(p_elem))
                    self.search_parent_object_mapping[search_string] = _search_element
                    _search_element.target.remove(p_elem)
                    return True

    def __exit__(self, exc_type, exc_value, traceback):
        rmtree(self.temp_dir)

    def _embed_icon_with_relationship(self, filename):
        """嵌入图标并返回关系ID"""
        file_ext = os.path.splitext(filename)[1].lower()
        icns_path = ICON_CONFIG.get(file_ext, ICON_DEFAULT_CONFIG)
        icon_path = generator_icon_picture(image_path=icns_path, text=filename,
                                           output_path=self.temp_dir / f"{uuid4().hex[:8]}.png",
                                           font_path=DEFAULT_FONT_PATH)
        if not os.path.exists(icon_path):
            raise FileNotFoundError(f"图标文件不存在: {icon_path}")

        os.makedirs(self.media_dir, exist_ok=True)
        icon_filename = f"icon_{uuid4().hex[:8]}{os.path.splitext(icon_path)[1]}"
        dest_path = self.media_dir / icon_filename
        copyfile(icon_path, dest_path)

        return self._add_relationship(IMAGE_TYPE_REFERENCE, f'media/{icon_filename}')

    def save(self):
        self._update_content_types()
        temp_save_base_dir = get_base_dir() / "temp_doc"
        os.makedirs(temp_save_base_dir, exist_ok=True)
        output_path = temp_save_base_dir / "output.docx"
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            for root, _, files in os.walk(self.temp_dir):
                for file in files:
                    # if file == '[Content_Types].xml':
                    #     continue
                    abs_path = os.path.join(root, file)
                    zip_path = os.path.relpath(abs_path, self.temp_dir)
                    new_zip.write(abs_path, zip_path)
        return Document(str(output_path))

    def get_target_id(self):
        return f'rId{self.relationship_count + 1}'

    def _update_content_types(self):
        """更新 Content_Types.xml 文件"""
        content_types_path = self.temp_dir / '[Content_Types].xml'
        try:
            if not content_types_path.exists():
                root = Element('Types', xmlns='http://schemas.openxmlformats.org/package/2006/content-types')
                tree = lxml.etree.ElementTree(root)
            else:
                tree = self._parse_xml(content_types_path)
                root = tree.getroot()

            content_type_map = {
                'bin': 'application/vnd.openxmlformats-officedocument.oleObject',
                'png': 'image/png',
                'jpeg': 'image/jpeg',
            }

            for ext, conent_type in content_type_map.items():
                xpath = f'//*[@ContentType="{conent_type}"]'
                if not root.xpath(xpath,
                                  namespaces={'ns': 'http://schemas.openxmlformats.org/package/2006/content-types'}):
                    elem = Element('Default', Extension=ext, ContentType=conent_type)
                    root.append(elem)

            # 保存修改
            with open(content_types_path, 'wb') as f:
                f.write(tostring(tree, encoding='UTF-8', xml_declaration=True))
        except Exception as e:
            print(f"更新 Content Types 失败: {str(e)}")

    @staticmethod
    def _get_ole_id():
        return f'oleObject{uuid4().hex[:8]}'

    @staticmethod
    def _get_file_data(file_path_list):
        for file_path in file_path_list:
            try:
                with open(file_path, 'rb') as f:
                    yield f.read(), file_path
            except TypeError:
                yield None, file_path

    @staticmethod
    def _parse_xml(path):
        return lxml.etree.parse(path)

    @staticmethod
    def _save_xml(tree, path):
        with open(path, 'wb') as f:
            f.write(tostring(tree, encoding='UTF-8', xml_declaration=True))

    @staticmethod
    def _get_progid(filename):
        ext = os.path.splitext(filename)[1].lower()
        progid_map = {
            '.xlsx': 'Excel.Sheet.12',
            '.docx': 'Word.Document.12',
            '.pptx': 'PowerPoint.Show.12',
            '.pdf': 'AcroExch.Document.11',
            '.doc': 'Word.Document.8',
            '.txt': 'txtfile',
            '.xmind': 'Package',
        }
        return progid_map.get(ext, 'Package')


def insert_files_to_docx(doc: Document, insert_mapping: dict[str, List[str]] = None) -> Document:
    with DocxOleEmbedderController(doc, insert_mapping) as ole_embedder:
        return ole_embedder.action()


if __name__ == '__main__':
    doc = Document("/Users/sheldon/Documents/GithubProject/Observer-Toolbox/xmindcase/output_real.docx")
    mapping = {
        "{file.zip}": ["/Users/sheldon/Documents/crm/2025/0430/V7.15版本_商用订单测试用例_lb_订单中心、咨询单.xmind"],
        "{bugs.xlsx}": ["/Users/sheldon/Documents/crm/2025/0430/V7.15版本_商用订单测试用例_lb_订单中心、咨询单.xmind"]
    }
    with DocxOleEmbedderController(doc, mapping) as ole_embedder:
        ole_embedder.action()
