from markdown import Markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor


class InlineDelete(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r"()~(.*?)~", "del"), "del", 0
        )


class InlineInsert(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r"()\+(.*?)\+", "ins"), "ins", 0
        )
