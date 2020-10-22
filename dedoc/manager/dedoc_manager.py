import copy
import os
import tempfile
from typing import Optional, List, Dict
from werkzeug.datastructures import FileStorage

from dedoc.data_structures.document_content import DocumentContent
from dedoc.configuration_manager import get_manager_config
from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.converters.file_converter import FileConverter
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.readers.doc_parser import DocParser
from dedoc.utils import get_unique_name


class DedocManager(object):
    def __init__(self, tmp_dir: Optional[str] = None):
        manager_config = get_manager_config()
        self.tmp_dir = tmp_dir

        if tmp_dir is not None and not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)

        converters = manager_config["converters"]
        self.converter = FileConverter(converters=converters)

        self.attachments_extractor = manager_config["attachments_extractor"]
        self.doc_parser = DocParser(readers=manager_config["readers"])
        self.structure_constructor = manager_config["structure_constructor"]
        self.document_metadata_extractor = manager_config["document_metadata_extractor"]

    def parse_file(self, file: FileStorage, parameters: Dict[str, str]) -> ParsedDocument:
        original_filename = file.filename.split("/")[-1]
        filename = get_unique_name(original_filename)

        if self.tmp_dir is None:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = os.path.join(tmp_dir, filename)
                file.save(tmp_path)
                return self.__parse_file(
                    tmp_dir=tmp_dir,
                    filename=filename,
                    parameters=parameters,
                    original_file_name=original_filename
                )

        tmp_path = os.path.join(self.tmp_dir, filename)
        file.save(tmp_path)
        return self.__parse_file(
            tmp_dir=self.tmp_dir,
            filename=filename,
            parameters=parameters,
            original_file_name=original_filename
        )

    def parse_existing_file(self, path: str, parameters: Dict[str, str]) -> ParsedDocument:
        with open(path, 'rb') as fp:
            file = FileStorage(fp, filename=path)
            return self.parse_file(file=file, parameters=parameters)

    def __parse_file(self, tmp_dir: str,
                     filename: str,
                     parameters: Dict[str, str],
                     original_file_name: str) -> ParsedDocument:
        """
        Function of complete parsing document with 'filename' with attachment files analyze
        """
        # Step 1 - Converting
        filename_convert = self.converter.do_converting(tmp_dir, filename)
        # Step 2 - Parsing content of converted file
        unstructured_document, contains_attachments = self.doc_parser.parse_file(
            tmp_dir=tmp_dir,
            filename=filename_convert,
            parameters=parameters
        )

        document_content = self.structure_constructor.structure_document(unstructured_document)

        # Step 3 - Adding meta-information
        parsed_document = self.__parse_file_meta(document_content=document_content,
                                                 directory=tmp_dir,
                                                 filename=filename,
                                                 original_file_name=original_file_name,
                                                 parameters=parameters)

        with_attachments = parameters.get("with_attachments", "False").lower() == "true"

        if with_attachments:
            parsed_attachment_files = self.__get_attachments(filename=filename_convert,
                                                             need_analyze_attachments=contains_attachments,
                                                             parameters=parameters,
                                                             tmp_dir=tmp_dir)
            parsed_document.add_attachments(parsed_attachment_files)

        return parsed_document

    def __parse_file_meta(self,
                          document_content: Optional[DocumentContent],
                          directory: str,
                          filename: str,
                          original_file_name: str,
                          parameters: dict) -> ParsedDocument:
        """
        Decorator with metainformation
        document_content - None for unsupported document in attachments
        """
        parsed_document = self.document_metadata_extractor.add_metadata(doc=document_content,
                                                                        directory=directory,
                                                                        filename=filename,
                                                                        original_filename=original_file_name,
                                                                        parameters=parameters)
        return parsed_document

    def __get_attachments(self,
                          filename: str,
                          need_analyze_attachments: bool,
                          parameters: dict,
                          tmp_dir: str) -> List[ParsedDocument]:
        parsed_attachment_files = []
        if need_analyze_attachments:
            attachment_files = self.attachments_extractor.get_attachments(tmp_dir=tmp_dir,
                                                                          filename=filename,
                                                                          parameters=parameters)
            for attachment in attachment_files:
                parameters_copy = copy.deepcopy(parameters)
                parameters_copy["is_attached"] = True
                parameters_copy["attachment"] = attachment
                try:
                    parsed_attachment_files.append(self.__parse_file(tmp_dir=tmp_dir,
                                                                     filename=attachment.get_filename_in_path(),
                                                                     parameters=parameters_copy,
                                                                     original_file_name=attachment.get_original_filename()
                                                                     ))
                except BadFileFormatException:
                    # return empty ParsedDocument with Meta information
                    parsed_attachment_files.append(
                        self.__parse_file_meta(document_content=None,
                                               directory=tmp_dir,
                                               filename=attachment.get_filename_in_path(),
                                               original_file_name=attachment.get_original_filename(),
                                               parameters=parameters_copy))

        return parsed_attachment_files
