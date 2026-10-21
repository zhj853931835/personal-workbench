# -*- coding: utf-8 -*-
"""Validate that index.html parses cleanly with no stray closing tags."""
import html.parser, io, sys

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


class Parser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.stray = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.stray.append(tag)
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.stack.pop()
            if self.stack:
                self.stack.pop()
        else:
            self.stray.append(tag)


def main(path="index.html"):
    with io.open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    p = Parser()
    p.feed(text)
    if p.stray:
        print("stray closing tags: %s" % p.stray[:10])
        return 1
    print("HTML parse OK; open tags at EOF: %d" % len(p.stack))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
