# pyright: strict

from typing import (TypeVar, Any, NamedTuple, cast)
from marko.ext.latex_renderer import LatexRenderer
import marko
import marko.block
import marko.inline
from marko import (inline, block, MarkoExtension)
from marko.source import (Source)
import re
import yaml
import sys
import io
from format_cpp import format_cpp

# https://github.com/python/typeshed/issues/3049
if isinstance(sys.stdin, io.TextIOWrapper) and sys.version_info >= (3, 7):
    sys.stdin.reconfigure(encoding="utf-8-sig")

class BlockElementWithPattern(block.BlockElement):
    priority=100
    pattern: re.Pattern[str] | str | None = None
    include_children=False
   
    def __init__(self, match: re.Match[str]) -> None:
        self.content = match.group(1)

    @classmethod
    def match(cls, source: Source) -> re.Match[str] | None:
        if cls.pattern is None:
            raise Exception('pattern not set')
        return source.expect_re(cls.pattern)

    @classmethod
    def parse(cls, source: Source) -> Any:
        m = source.match
        source.consume()
        return m

class BlockMathInParagraph(inline.InlineElement):
    priority=101
    pattern = r'\$\$([\s\S]*?)\$\$'
    parse_children = False
   
    def __init__(self, match: re.Match[str]) -> None:
        self.content = match.group(1)
    
class InlineMath(inline.InlineElement):
    priority=100
    pattern = r'\$([\s\S]*?)\$'
    parse_children = False
    
    def __init__(self, match: re.Match[str]) -> None:
        self.content = match.group(1)
        
class BlockMath(BlockElementWithPattern):
    pattern=re.compile(r'\$\$([\s\S]*?)\$\$', flags=re.M)
    
class FrontMatter(BlockElementWithPattern):
    priority=100
    pattern = re.compile(r'---\n(.*?)\n---\n', re.M | re.DOTALL)
    parse_children = False
    def __init__(self, match: re.Match[str]) -> None:
        super().__init__(match)
        self.data = yaml.safe_load(self.content)
        
class LatexTabular(BlockElementWithPattern):
    pattern = re.compile(r'(\\begin\{tabular\}[\s\S]*\\end\{tabular\})', re.M)
    
class LatexTabularx(BlockElementWithPattern):
    pattern = re.compile(r'(\\begin\{tabularx\}[\s\S]*\\end\{tabularx\})', re.M)
    
class LatexLongTable(BlockElementWithPattern):
    pattern = re.compile(r'(\\begin\{longtable\}[\s\S]*\\end\{longtable\})', re.M)
    
class LatexMinipage(BlockElementWithPattern):
    pattern = re.compile(r'(\\begin\{minipage\}[\s\S]*\\end\{minipage\})', re.M)
    
class CustomFootnote(inline.InlineElement):
    pattern=r'\[\{(.*)\}\]'
    parse_children = False
    
    def __init__(self, match: re.Match[str]) -> None:
        self.content = match.group(1)
        
class Strikethrough(inline.InlineElement):
    pattern=r'\~\~(.*)\~\~'
    parse_children = False
    
    def __init__(self, match: re.Match[str]) -> None:
        self.content = match.group(1)
        
class Emoji(inline.InlineElement):
    pattern=r'\:(.*)\:'
    parse_children = False
    
    def __init__(self, match: re.Match[str]) -> None:
        self.emoji_name = match.group(1)
        
class InterviewQA(inline.InlineElement):
    pattern=r'([QA])\: '
    parse_children = False
    def __init__(self, match: re.Match[str]) -> None:
        self.type = match.group(1)
        
shorthand_data = yaml.safe_load(open('./shorthands.yaml'))
class ShorthandMeaning(NamedTuple):
    value: str
    id: int

transformed_shorthand_data: dict[str, ShorthandMeaning] = {}
for idx, data in enumerate(shorthand_data):
    for keyword, meaning in data.items():
        transformed_shorthand_data[keyword] = ShorthandMeaning(meaning, idx)
        
class Shorthand(inline.InlineElement):
    pattern = f'({"|".join(transformed_shorthand_data.keys())})'
    parse_children = False
    def __init__(self, match: re.Match[str]) -> None:
        self.keyword = match.group(1)
        self.meaning = transformed_shorthand_data[self.keyword]

class MarkoLatexRenderer(LatexRenderer):
    front_matter: dict[str, Any] = {}
    added_shorthand: set[int] = set()
    
    def render_document(self, element: marko.block.Document):
        children = self.render_children(element)
        
        layout = self.front_matter.get('layout')

        if type(layout) != str:
            raise Exception('layout is unset')

        meta = cast(dict[str, str], self.front_matter.get('meta'))
        return self._environment2(
            layout,
            children,
            meta
        )
    
    def render_heading(self, element: marko.block.Heading):
        """
        Override to get the artile name from the H1 heading.
        """
        children = self.render_children(element)
        if element.level == 1:
            self.article_name = children
            return ""

        # ignore since we can not type the super class _directly_.
        return super().render_heading(element)  # pyright: ignore
    
    def render_fenced_code(self, element: marko.block.FencedCode):
        language = self._escape_latex(element.lang).strip().lower()
        if 'c++' in language or 'cpp' in language:
            language = 'cpp'
        if 'py' in language or 'python' in language:
            language = 'python'
        if language not in ['c', 'cpp', 'python', 'text']:
            language = 'text'

        # This cast got from the marko source code (marko.block.FencedCode#__init__)
        content: str = cast(marko.inline.RawText, element.children[0]).children
        if language == 'cpp':
            content = format_cpp(content)
        return self._environment(f"{language}code", content)
    
    def render_block_math(self, element: BlockMath):
        # print('block math', element.content)
        return f"$${element.content}$$"
    
    def render_block_math_in_paragraph(self, element: BlockMathInParagraph):
        # print('block math in paragraph', element.content)
        return f"$${element.content}$$"
    
    def render_inline_math(self, element: InlineMath):
        # print('inline math', element.content)
        return f"${element.content}$"
    
    def render_link(self, element: marko.inline.Link):
        if element.title:
            print("Setting a title for links is not supported!")
        body = self.render_children(element)
        # return f"\\href{{{element.dest}}}{{{body}}} \\footnote{{{self._escape_latex(element.dest)}}}"
        return f"\\insertLink{{ {self._escape_latex(element.dest)} }}{{ {body} }}"
    
    def render_list(self, element: marko.block.List):
        children = self.render_children(element)
        env = "enumerate" if element.ordered else "itemize"
        # TODO: check how to handle element.start with ordered list
        if element.start and element.start != 1:
            print("Setting the starting number of the list is not supported!")
        return self._environment(env, children, ['leftmargin=0.5cm', 'itemsep=1mm', 'topsep=0mm', 'partopsep=0mm', 'parsep=0mm'])
            
    def render_image(self, element: marko.inline.Image):
        children = self.render_children(element)
        
        return f"\\includeImage{{ {element.dest} }}{{ {children} }}"
        
    def render_custom_footnote(self, element: CustomFootnote):
        return f"\\footnote{{ {element.content} }}"
    
    def render_strikethrough(self, element: Strikethrough):
        return f"\\sout{{ {element.content} }}"
    
    def render_html_block(self, element: marko.block.HTMLBlock):
        print("Rendering HTML is not supported!")
        print(element.children)
        return ""
    
    def render_latex_tabular(self, element: LatexTabular):
        return r'\begin{center}' + element.content + r'\end{center}'
    
    def render_latex_tabularx(self, element: LatexTabularx):
        return r'\begin{center}' + element.content + r'\end{center}'
    
    def render_latex_long_table(self, element: LatexLongTable):
        return r'\begin{center}' + element.content + r'\end{center}'
    
    def render_latex_minipage(self, element: LatexMinipage):
        return r'\begin{center}' + element.content + r'\end{center}'
    
    def render_emoji(self, element: Emoji):
        return f'\\{element.emoji_name}'
    
    def render_line_break(self, element: Any):
        # always soft
        return '\n'
    
    def render_front_matter(self, element: FrontMatter):
        self.front_matter = element.data
        return ''
    
    def render_interview_qa(self, element: InterviewQA):
        if self.front_matter.get('layout') == 'interview':
            return r'\interview' + element.type + ' '
        return element.type + ': '
    
    def render_shorthand(self, element: Shorthand):
        if element.meaning.id in self.added_shorthand:
            return element.keyword
        self.added_shorthand.add(element.meaning.id)
        return f'\\shorthand{{{element.keyword}}}{{{element.meaning.value}}}'
    
    @staticmethod
    def _escape_latex(text: str) -> str:
        # print('escaping', text)
        # Special LaTeX Character:  # $ % ^ & _ { } ~ \
        specials = {
            "#": "\\#",
            "$": "\\$",
            "%": "\\%",
            "&": "\\&",
            "_": "\\_",
            "{": "\\{",
            "}": "\\}",
            "^": "\\^{}",
            "~": "\\~{}",
            "\\": "\\textbackslash{}",
            "\"": "''"
        }

        return "".join(specials.get(s, s) for s in text)
    
    @staticmethod
    def _environment2(env_name: str, content: str, options: dict[str,  str] = {}) -> str:
        options_str = '\n'.join(map(lambda item: f'  {item[0]}={{{item[1]}}},', options.items()))
        return f"\\begin{{{env_name}}}[\n{options_str}\n]\n{content}\\end{{{env_name}}}\n"

def make_extension():
    return MarkoExtension(
        elements=[
                BlockMath,
                BlockMathInParagraph,
                InlineMath,
                CustomFootnote,
                Strikethrough,
                LatexTabular,
                LatexLongTable,
                LatexMinipage,
                LatexTabularx,
                Emoji,
                FrontMatter,
                InterviewQA,
                Shorthand
            ],
        renderer_mixins = [MarkoLatexRenderer]
    )
