from inspect import cleandoc

from pyconlang import PYCONLANG_PATH
from pyconlang.cli import compile_book


def test_book(simple_pyconlang):
    (simple_pyconlang / "grammar.md").write_text(
        cleandoc(
            """
        **This is an example: #*kika@era1 <stone>.PL#**
        
        !translate
        
        *kika@era1 
        <stone>.PL
        
        !translate
        """
        )
        + "\n"
    )

    compile_book()

    html = (PYCONLANG_PATH / "output.html").read_text()

    assert "By Mr. Tester" in html
    assert "TestLang" in html

    assert (
        "<p><strong>This is an example: <span>kiga abagigi</span></strong></p>" in html
    )

    assert "<pre><code>kiga\nabagigi\n</code></pre>" in html

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
