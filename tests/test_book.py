from inspect import cleandoc

from pyconlang import PYCONLANG_PATH
from pyconlang.cli import compile_book


def test_details(simple_pyconlang):
    write(
        simple_pyconlang / "grammar.md",
        """
    !details:The summary
    
    The information is here
    and here
    
    !details
    """,
    )

    html = compile()

    assert (
        "<details>\n<summary>The summary</summary>\n<p>The information is here\nand here</p>\n</details>"
        in html
    )


def test_table(simple_pyconlang):
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

    html = compile()

    assert '<th colspan="2">c1,1-2</th>' in html

    assert '<td rowspan="2">c2-3,3</td>' in html

    assert '<th colspan="2" rowspan="3">c3-5,1-2</th>' in html


def test_container(simple_pyconlang):
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

    html = compile()

    assert '<span class="inline">test span1</span>' in html
    assert '<div class="block">\n<p>test div</p>\n</div>' in html
    assert "<div>\n<p>test div clean</p>\n</div>" in html


def test_book(simple_pyconlang):
    write(
        simple_pyconlang / "grammar.md",
        """
      **This is an example: #*kika@era1 <stone>.PL#**
      
      !translate
      
      *kika@era1 
      <stone>.PL
      
      !translate
      """,
    )

    html = compile()

    assert "By Mr. Tester" in html
    assert "TestLang" in html

    assert (
        "<p><strong>This is an example: <span>kiga abagigi</span></strong></p>" in html
    )

    assert (
        cleandoc(
            """
                <pre><code>&ast;kika@era1  =&gt; kiga
                &lt;stone&gt;.PL =&gt; abagigi
                </code></pre>
                """
        )
        in html
    )

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

    k_index = html.index("K</h2>")
    l_index = html.index("L</h2>")
    entry_index = html.index("kibu")

    assert k_index < entry_index < l_index


def write(path, text):
    path.write_text(cleandoc(text) + "\n")


def compile():
    compile_book()

    return (PYCONLANG_PATH / "output.html").read_text()
