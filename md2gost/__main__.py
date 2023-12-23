#!/bin/python
import click
import os.path
import sys

from . import __version__


class DeprecatedOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.deprecated = kwargs.pop('deprecated', ())
        self.preferred = kwargs.pop('preferred', args[0][-1])
        super(DeprecatedOption, self).__init__(*args, **kwargs)


@click.command
@click.argument("filenames", nargs=-1)
@click.option("-o", "--output", help="Путь до сгенерированного файла")
@click.option("-t", "--template", help="Путь до шаблона в формате docx")
@click.option("-T", "--title", help="Путь до титульника в формате docx")
@click.option("-f", "--first-page", help="Номер первой страницы", default=1)
@click.option("-s", "--syntax-highlighting", help="Подсветка синтаксиса в листингах", is_flag=True)
@click.option("--title-pages", hidden=True)
@click.option("-d", "--debug", is_flag=True, hidden=True)
@click.version_option(__version__, "--version", "-v")
@click.help_option("-h", "--help")
def main(filenames: tuple[str, ...], output: str, template: str, title: str, first_page: int,
         syntax_highlighting: bool, debug: bool, title_pages: str):
    # deprecated options
    if title_pages:
        print("Параметр --title-pages устарел. Используйте --first-page.", file=sys.stderr)
        sys.exit(1)

    from .converter import Converter

    if not filenames:
        print("Нет входных файлов!")
        return -1

    if not output:
        output = os.path.basename(filenames[0]).replace(".md", ".docx")

    if not template:
        template = os.path.join(os.path.dirname(__file__), "Template.docx")

    converter = Converter(template, title, first_page, debug, syntax_highlighting)
    converter.convert(filenames, output)

    print(f"Сгенерированный документ: {os.path.abspath(output)}")

    if debug:
        import platform
        if platform.system() == 'Darwin':       # macOS
            import subprocess
            subprocess.call(('open', output))
        elif platform.system() == 'Windows':    # windows
            os.startfile(output)
        else:                                   # linux variants
            import subprocess
            subprocess.call(('xdg-open', output))


if __name__ == "__main__":
    sys.exit(main())
