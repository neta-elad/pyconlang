from pyconlang.cli import run_repl


def test_repl(capsys, mock_input, simple_pyconlang):
    mock_input.send_text("apaki\n")
    mock_input.close()

    run_repl()

    captured = capsys.readouterr()

    assert captured.out == "abashi\nGoodbye.\n"
