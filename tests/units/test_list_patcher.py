import unittest
from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.structure_constructor.concreat_structure_constructors.list_patcher import ListPatcher
from dedoc.structure_parser.heirarchy_level import HierarchyLevel


class TestListPatcher(unittest.TestCase):
    patcher = ListPatcher()

    def __get_text(self, lines: List[LineWithMeta]) -> List[str]:
        return [line.line for line in lines]

    def __get_line(self, text: str, level1: int, level2: int, hl: str = "list") -> LineWithMeta:
        hierarchy_level = HierarchyLevel(level1, level2, False, hl)
        metadata = ParagraphMetadata("list_item", None, 0, None)
        return LineWithMeta(text, hierarchy_level=hierarchy_level, metadata=metadata, annotations=[])

    def test_correct_list(self):
        line1 = self.__get_line("1  item", 1, 0)
        line2 = self.__get_line("2  item", 1, 0)
        line3 = self.__get_line("2.1  item", 1, 1)
        line4 = self.__get_line("2.2  item", 1, 0)
        line5 = self.__get_line("3  item", 1, 0)
        lines = [line1, line2, line3, line4, line5]
        result = self.patcher.patch(lines)
        self.assertListEqual(self.__get_text(lines), self.__get_text(result))

    def test_miss_in_the_middle_list1(self):
        line1 = self.__get_line("1 item", 1, 0)
        line3 = self.__get_line("2.1  item", 1, 1)
        line4 = self.__get_line("2.2  item", 1, 0)
        line5 = self.__get_line("3  item", 1, 0)
        lines = [line1, line3, line4, line5]
        result = self.patcher.patch(lines)
        self.assertListEqual(["1 item", "2.", "2.1  item", "2.2  item", "3  item"], self.__get_text(result))

    def test_miss_in_the_middle_list2(self):
        line1 = self.__get_line("1 item", 1, 0)
        line3 = self.__get_line("2.1.2.1.2  item", 1, 1)
        line4 = self.__get_line("2.2  item", 1, 0)
        line5 = self.__get_line("3  item", 1, 0)
        lines = [line1, line3, line4, line5]
        result = self.patcher.patch(lines)
        expected = ["1 item", "2.", "2.1.", "2.1.1.", "2.1.2.", "2.1.2.1.", "2.1.2.1.1.", "2.1.2.1.2  item",
                    "2.2  item", "3  item"]
        self.assertListEqual(expected, self.__get_text(result))

    def test_hl_raw_text(self):
        line1 = self.__get_line("1 item", None, None, HierarchyLevel.raw_text)
        line3 = self.__get_line("2.1.2.1.2  item", 1, 1)
        line4 = self.__get_line("2.2  item", 1, 0)
        line5 = self.__get_line("3  item", 1, 0)
        lines = [line1, line3, line4, line5]
        result = self.patcher.patch(lines)
        expected = ["1 item", "2.", "2.1.", "2.1.1.", "2.1.2.", "2.1.2.1.", "2.1.2.1.1.", "2.1.2.1.2  item",
                    "2.2  item", "3  item"]
        self.assertListEqual(expected, self.__get_text(result))

    def test_hl_raw_text2(self):
        line1 = self.__get_line("1 item", None, None, HierarchyLevel.raw_text)
        line3 = self.__get_line("2.1.2.1.2  item", None, None, HierarchyLevel.raw_text)
        line4 = self.__get_line("2.2  item", None, None, HierarchyLevel.raw_text)
        line5 = self.__get_line("3  item", None, None, HierarchyLevel.raw_text)
        lines = [line1, line3, line4, line5]
        result = self.patcher.patch(lines)
        expected = ["1 item", "2.", "2.1.", "2.1.1.", "2.1.2.", "2.1.2.1.", "2.1.2.1.1.", "2.1.2.1.2  item",
                    "2.2  item", "3  item"]
        self.assertListEqual(expected, self.__get_text(result))

    def test_hl_raw_text3(self):
        line1 = self.__get_line("2. item", None, None, HierarchyLevel.raw_text)
        line3 = self.__get_line("2.1.2.1.2  item", None, None, HierarchyLevel.raw_text)
        line4 = self.__get_line("2.2  item", None, None, HierarchyLevel.raw_text)
        line5 = self.__get_line("3  item", None, None, HierarchyLevel.raw_text)
        lines = [line1, line3, line4, line5]
        result = self.patcher.patch(lines)
        expected = ["2. item", "2.1.", "2.1.1.", "2.1.2.", "2.1.2.1.", "2.1.2.1.1.", "2.1.2.1.2  item",
                    "2.2  item", "3  item"]
        self.assertListEqual(expected, self.__get_text(result))

    def test_hl_raw_text4(self):
        line1 = self.__get_line("2 item", None, None, HierarchyLevel.raw_text)
        line2 = self.__get_line("some item", None, None, HierarchyLevel.raw_text)
        line3 = self.__get_line("2 item", None, None, HierarchyLevel.raw_text)

        lines = [line1, line2, line3]
        result = self.patcher.patch(lines)
        expected = ["2 item", "some item", "2 item"]
        self.assertListEqual(expected, self.__get_text(result))

    def test_hl_raw_text5(self):
        line1 = self.__get_line("1 item", None, 1, HierarchyLevel.raw_text)
        line3 = self.__get_line("1.1  item", 1, 5)
        line4 = self.__get_line("2.2  item", 1, 2)
        line5 = self.__get_line("3  item", 1, 0)
        lines = [line1, line3, line4, line5]
        result = self.patcher.patch(lines)
        expected = ["1 item", "1.1  item", "2.", "2.1.", "2.2  item", "3  item"]
        self.assertListEqual(expected, self.__get_text(result))

    def test_empty_list(self):
        lines = []
        result = self.patcher.patch(lines)
        self.assertListEqual([], self.__get_text(result))

    def test_miss_head_element_list1(self):
        line2 = self.__get_line("2  item", 1, 0)
        line3 = self.__get_line("2.1  item", 1, 1)
        line4 = self.__get_line("2.2  item", 1, 0)
        line5 = self.__get_line("3  item", 1, 0)
        lines = [line2, line3, line4, line5]
        result = self.patcher.patch(lines)
        self.assertListEqual(self.__get_text(lines), self.__get_text(result))

    def test_miss_head_element_list2(self):
        line3 = self.__get_line("2.1  item", 1, 1)
        line4 = self.__get_line("2.2  item", 1, 0)
        line5 = self.__get_line("3  item", 1, 0)
        lines = [line3, line4, line5]
        result = self.patcher.patch(lines)
        self.assertListEqual(self.__get_text(lines), self.__get_text(result))
