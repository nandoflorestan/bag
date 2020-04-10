"""Tests the *text* module."""

import unittest
from bag.text import break_lines_near, to_filename


class TestText(unittest.TestCase):

    def test_to_filename(self):
        self.assertEqual(
            to_filename("Carl Sagan", for_web=True, maxlength=16),
            'Carl-Sagan')


class TestBreakLinesNear(unittest.TestCase):
    def test_works_like_this(self):
        assert break_lines_near("duas palavras", 20) == ["duas palavras"]
        assert break_lines_near("tres palavras diferentes", 20) == [
            "tres palavras difer…",
            "…entes",
        ]
        assert break_lines_near(
            "trespalavras detamanho mediopragrande", 15
        ) == ["trespalavras", "detamanho medi…", "…opragrande"]
        assert break_lines_near("umapalavraso", 7) == ["umapal…", "…avraso"]
        assert break_lines_near("umapalavragigantesca mas com outras", 15) == [
            "umapalavragiga…",
            "…ntesca mas com",
            "outras",
        ]
        assert break_lines_near(
            "umapalavradetamanhocompletamentedesnecessarioporemvalidoparaeste"
            "teste somadaaoutrapalavratambemcompletamentedesnecessaria",
            70,
        ) == [
            "umapalavradetamanhocompletamentedesnecessarioporemvalidoparaeste"
            "teste",
            "somadaaoutrapalavratambemcompletamentedesnecessaria",
        ]
        assert break_lines_near(
            "um texto completo cheio de espacos e caracteres whitespace "
            "altamente significativos ou nao",
            30,
        ) == [
            "um texto completo cheio de",
            "espacos e caracteres whitespa…",
            "…ce altamente significativos",
            "ou nao",
        ]
        assert break_lines_near(
            "um texto completo cheio de\respacos e caracteres whitespace "
            "altamente significativos\nou nao mas nao importa oque\t"
            "importa e o teste",
            30,
        ) == [
            "um texto completo cheio de",
            "espacos e caracteres whitespa…",
            "…ce altamente significativos",
            "ou nao mas nao importa oque",
            "importa e o teste",
        ]
        assert break_lines_near("", 10) == []
        assert break_lines_near("textolongoparatest", 10, leeway=0) == [
            "textolong…",
            "…oparatest",
        ]
        assert break_lines_near(
            "textolongoparatest", 10, end_line_break="", start_line_break="--"
        ) == ["textolongo", "--paratest"]
        assert break_lines_near(
            "textolongoparatest", 10, end_line_break="--", start_line_break=""
        ) == ["textolon--", "goparatest"]
        assert break_lines_near(
            "textolongoparatest", 10, end_line_break="", start_line_break=""
        ) == ["textolongo", "paratest"]

    def test_raises_when_arguments_make_no_sense(self):
        with self.assertRaises(AssertionError):
            break_lines_near("duas palavras", 20, leeway=-1)
        with self.assertRaises(AssertionError):
            break_lines_near("duas palavras", length=0)
