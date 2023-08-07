from pyrsercomb import default, lift4, regex, string, token

from .domain import TraceLine

word = regex(r"[^\s:]+")
to = (-(token(string("to")) >> token(word)))[default(lambda: "")]
trace_line = (
    token(string("Applied")) >> token(word)
    & to << token(string(":"))
    & token(word) << token(string("->"))
    & token(word)
)[lift4(TraceLine)]

trace_line_heading = (token(string("Tracing")) << regex(r".*"))[lambda _: None]

any_trace_line = trace_line_heading ^ trace_line
