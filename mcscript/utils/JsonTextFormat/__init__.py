from importlib import resources

from lark import Lark

markupGrammar = Lark(
    resources.read_text("mcscript", "textMarkup.lark"),
    parser="lalr",
    maybe_placeholders=True
)

if __name__ == '__main__':
    text = "[b]McScript[/b] Hello, [b][i][color=red]{}[/color][/i][/b]"
    print(markupGrammar.parse(text).pretty())
