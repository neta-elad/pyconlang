from inspect import cleandoc
from pathlib import Path

from pyconlang import PYCONLANG_PATH
from pyconlang.book import compile_book


def test_details(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "grammar.md",
        """
    !details:The summary
    
    The information is here
    and here
    
    !details
    """,
    )

    html = read()

    assert (
        "<details>\n<summary>The summary</summary>\n<p>The information is here\nand here</p>\n</details>"
        in html
    )


def test_table(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "book.md",
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
        simple_pyconlang / "grammar.md",
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
        simple_pyconlang / "book.md",
        """
          
          r{<stone>} r{*kika} 
          
          ph{*kika} 
          
          pr{<stone>} pr{*kika}
          
          d{<stone>} d{.PL}
          
          """,
    )

    html = read()

    assert "abak" in html
    assert "shiga" in html
    assert "ʃiga" in html
    assert "apak" in html
    assert "kika" in html
    assert "(n.) stone, pebble" in html
    assert "plural for inanimate" in html


def test_advanced_macros(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "book.md",
        """

          r[<stone>] r[*kika] 
          r[<gravel> <stone> *kika]

          ph[*kika]

          pr[<stone>] pr[*kika]
          pr[<gravel> <.PL>]
          
          d[<stone>]
          
          d[.PL]
          
          d[<gravel>.COL]
          """,
    )

    html = read()

    assert "<strong>abak</strong>" in html
    assert "<strong>shiga</strong>" in html
    assert "<strong>abagigi abak shiga</strong>" in html
    assert "<ruby><strong>shiga</strong> <rt>[ʃiga]</rt></ruby>" in html
    assert "<em>*apak</em>" in html
    assert "<em>*kika</em>" in html
    assert "<em>*iki</em>" in html
    assert "<em>*apak</em> + <em>*iki</em>" in html

    assert '<abbr title="(n.) stone, pebble">stone</abbr>' in html
    assert '.<abbr title="plural for inanimate">PL</abbr>' in html
    assert (
        '<abbr title="(n.) gravel">gravel</abbr>.<abbr title="collective">COL</abbr>'
        in html
    )


def test_before_after(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "book.md",
        """
          >r[<stone>]
          >ph[*kika]
          
          r<[<stone>]
          ph<[*kika]
        """,
    )

    html = read()

    print(html)

    assert "<em>*apak</em> &gt; <strong>abak</strong>" in html
    assert "<strong>abak</strong> &lt; <em>*apak</em>" in html
    assert (
        "<em>*kika</em> &gt; <ruby><strong>shiga</strong> <rt>[ʃiga]</rt></ruby>"
        in html
    )
    assert (
        "<ruby><strong>shiga</strong> <rt>[ʃiga]</rt></ruby> &lt; <em>*kika</em>"
        in html
    )


def test_gloss_table(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "grammar.md",
        """
          
          g[<stone>.PL <gravel>.PL]
          
          """,
    )

    html = read()

    assert (
        "<th><ruby><strong>abagigi</strong> <rt>[abagigi]</rt></ruby></th>\n"
        + "<th><ruby><strong>abagigiigi</strong> <rt>[abagigiigi]</rt></ruby></th>"
        in html
    )

    assert (
        '<td><abbr title="(n.) stone, pebble">stone</abbr>.<abbr title="plural for inanimate">PL</abbr></td>\n'
        + '<td><abbr title="(n.) gravel">gravel</abbr>.<abbr title="plural for inanimate">PL</abbr></td>'
        in html
    )


def test_metadata(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "grammar.md",
        """
          this $name is written by ${author}!
          """,
    )

    html = read()

    assert "this TestLang is written by Mr. Tester!" in html


def test_grouping(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "grammar.md",
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

    assert (
        "<p><strong>abagigi</strong> [abagigi] <em>*apak</em> + <em>*iki</em> (n.) gravel</p>"
        in html
    )

    assert (
        "<p><strong>abak</strong>, <strong>abagigi</strong> [abak] <em>*apak</em> (n.) stone, pebble</p>"
        in html
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


def test_unicode_escape(simple_pyconlang: Path) -> None:
    write(
        simple_pyconlang / "book.md",
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
        simple_pyconlang / "book.md",
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


def write(path: Path, text: str) -> None:
    path.write_text(cleandoc(text) + "\n")


def read() -> str:
    compile_book()

    return (PYCONLANG_PATH / "output.html").read_text()
