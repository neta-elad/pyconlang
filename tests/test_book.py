from inspect import cleandoc
from pathlib import Path

import pytest
from pyrsercomb import PyrsercombError

from pyconlang.book import OUT_PATH, compile_book


def test_table(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/index.out.md",
        """
        |c1,1-2|<|c1,3|c1,4|
        |-------|-|----|-----|
        |c2,1|c2,2|c2-3,3|c2,4|
        |c3-5,1-2 >|<|  ^   |c3,4|
        |    ^   |<|c4,3|c4,4|
        |    ^   |<|c5,3|c5,4|
        
        """,
    )

    html = read()

    assert '<th colspan="2">c1,1-2</th>' in html

    assert '<td rowspan="2">c2-3,3</td>' in html

    assert '<th colspan="2" rowspan="3">c3-5,1-2</th>' in html


def test_container(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/grammar.md",
        """
    
        &{test span1}{: .inline }
        
        &{
        
        test div
        
        }{: .block }
        
        &{
        
        test div clean
        
        }
        
        """,
    )

    html = read()

    assert '<span class="inline">test span1</span>' in html
    assert '<div class="block">\n<p>test div</p>\n</div>' in html
    assert "<div>\n<p>test div clean</p>\n</div>" in html


def test_raw_macros(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/index.out.md",
        """
          
          r(<stone>) r(*kika) 
          
          ph(*kika) 
          
          pr(<stone>) pr(*kika)
          
          d(<stone>) d(.PL)
          
          r(% <stone>)
          r({scope:ultra-modern} <gravel>)
          
          """,
    )

    html = read()

    assert "kaba" in html
    assert "shiga" in html
    assert "ʃiga" in html
    assert "apak" in html
    assert "kika" in html
    assert "(n.) stone, pebble" in html
    assert "plural for inanimate" in html
    assert "apak" in html
    assert "kibiishimi" in html


def test_advanced_macros(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/index.out.md",
        """

          r[<stone>] r[*kika] 
          r[<gravel> <stone> *kika]

          ph[*kika]

          pr[<stone>] pr[*kika]
          pr[<gravel> <.PL>]
          
          d[<stone>]
          
          d[.PL]
          
          d[<gravel>.COL]
          
          ph[%ultra-modern <gravel>]
          d[%ultra-modern <gravel>]
          """,
    )

    html = read()

    assert "<strong>kaba</strong>" in html
    assert "<strong>shiga</strong>" in html
    assert "<strong>kabaigi kaba shiga</strong>" in html
    assert "<ruby><strong>shiga</strong><rt>[ʃiga]</rt></ruby>" in html
    assert "<ruby><strong>kibiishimi</strong><rt>[kibiiʃimi]</rt></ruby>" in html
    assert "<em>*kapa</em>" in html
    assert "<em>*kika</em>" in html
    assert "<em>*iki</em>" in html
    assert "<em>*kapa</em> + <em>*iki</em>" in html

    assert '<abbr title="(n.) stone, pebble">stone</abbr>' in html
    assert '.<abbr title="plural for inanimate">PL</abbr>' in html
    assert (
        '<abbr title="(n.) gravel">gravel</abbr>.<abbr title="collective">COL</abbr>'
        in html
    )
    assert '<abbr title="(n.) gravel [ultra-modern]">gravel</abbr>' in html


def test_before_after(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/index.out.md",
        """
          >r[<stone>]
          >ph[*kika]
          
          r<[<stone>]
          ph<[*kika]
        """,
    )

    html = read()

    assert "<em>*kapa</em> &gt; <strong>kaba</strong>" in html
    assert "<strong>kaba</strong> &lt; <em>*kapa</em>" in html
    assert (
        "<em>*kika</em> &gt; <ruby><strong>shiga</strong><rt>[ʃiga]</rt></ruby>" in html
    )
    assert (
        "<ruby><strong>shiga</strong><rt>[ʃiga]</rt></ruby> &lt; <em>*kika</em>" in html
    )


def test_gloss_table(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/grammar.md",
        """
          
          g[<stone>.PL <gravel>.PL]
          
          
          g[%ultra-modern <gravel>]
          
          
          """,
    )

    html = read()

    assert (
        "<th><ruby><strong>kabaigi</strong><rt>[kabaigi]</rt></ruby></th>\n"
        "<th><ruby><strong>ka</strong><rt>[ka]</rt></ruby></th>" in html
    )

    assert (
        '<td><abbr title="(n.) stone, pebble">stone</abbr>.<abbr title="plural for inanimate">PL</abbr></td>\n'
        '<td><abbr title="(n.) gravel">gravel</abbr>.<abbr title="plural for inanimate">PL</abbr></td>'
        in html
    )

    assert (
        "<th><ruby><strong>kibiishimi</strong><rt>[kibiiʃimi]</rt></ruby></th>" in html
    )

    assert '<td><abbr title="(n.) gravel [ultra-modern]">gravel</abbr></td>' in html


def test_config(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/grammar.md",
        """
          this $name is written by ${author}!
          """,
    )

    html = read()

    assert "this TestLang is written by Mr. Tester!" in html


def test_grouping(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/grammar.md",
        cleandoc(
            """
          
          before group
          
          !group
          &#this
          &#that
          &#also
          !group
          
          after group
          
          """
        ),
    )

    html = read()

    a_index = html.index("A</h2>")
    t_index = html.index("T</h2>")

    this_index = html.index("#this</p>")
    that_index = html.index("#that</p>")
    also_index = html.index("#also</p>")

    assert a_index < also_index < t_index < that_index < this_index


def test_dictionary(simple_pyconlang: Path) -> None:
    html = read()

    assert "<p><strong>ka</strong> [ka] <em>*ka</em> (n.) gravel (plural)</p>" in html

    assert (
        "<p><strong>kabaigi</strong> [kabaigi] <em>*kapa</em> + <em>*iki</em> (n.) gravel</p>"
        in html
    )

    assert (
        "<p><strong>kaba</strong> [kaba] <em>*kapa</em> (n.) stone, pebble</p>" in html
    )

    assert "<p><strong>ishi</strong> [iʃi] <em>*iki</em> (adj.) big, great</p>" in html

    assert '<h2 id="k">K</h2>' in html
    assert (
        "<p><strong>kibu</strong> [kibu] <em>*kipu</em> (adj.) strong, stable</p>"
        in html
    )

    i_index = html.index("I</h2>")
    k_index = html.index("K</h2>")
    entry_index = html.index("kibu")

    assert i_index < k_index < entry_index


def test_affixes(simple_pyconlang: Path) -> None:
    html = read()

    assert '<h1 id="affixes-table">Affixes Table</h1>' in html
    assert (
        "<td>-<ruby><strong>ishima</strong><rt>[iʃima]</rt></ruby></td>\n"
        "<td>distributive plural</td>\n"
        "<td><em>*iki</em>, <em>*ma</em></td>"
    ) in html


def test_unicode_escape(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/index.out.md",
        """
          
          \\u0041\\u0043\\u0045
          
          \\u0026ph{<stone>}
          
          """,
    )

    html = read()

    assert "ACE" in html
    assert "&amp;ph{<stone>}"


def test_skip(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/index.out.md",
        """
        ! this line appears
        !! this one doesn't
        !!! and this one also doesn't
        """,
    )

    html = read()

    assert "! this line appears" in html
    assert "this one doesn't" not in html
    assert "and this one also doesn't" not in html


def test_errors(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "src/index.out.md",
        """
        r[<book]
        """,
    )

    with pytest.raises(PyrsercombError):
        read()

    write(
        simple_pyconlang / "src/lexicon.pycl",
        """
        bla
        """,
    )

    with pytest.raises(PyrsercombError):
        read()


def test_assets(simple_pyconlang: Path) -> None:
    write(simple_pyconlang / "assets/test.txt", "bla")
    read()
    assert (OUT_PATH / "test.txt").read_text() == "bla\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cleandoc(text) + "\n")


def read() -> str:
    compile_book()

    return (OUT_PATH / "index.html").read_text()
