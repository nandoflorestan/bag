#! /usr/bin/env python3
"""A simple command to replace text in many files, without regular expressions.

Usage::

    replace_many -d DIRECTORY '.py,.jinja2' 'text being sought' 'replacement text'
"""

from argh import ArghParser, arg  # pip install argh

from bag.pathlib_complement import Path


@arg("extensions", help="Comma-separated file extensions to search")
@arg("text", help="The text being sought")
@arg("replace", help="The replacement text")
@arg("dir", help="Directory to be walked")
def replace_many(
    extensions: str,
    text: str,
    replace: str,
    dir: str = ".",
):
    """Replace text in multiple files."""
    directory = Path(dir).resolve()
    assert directory.is_dir(), "*dir* must be a directory, not a file."
    exts = tuple((e.strip() for e in extensions.split(",")))

    print(f"Replacing in {directory}:")
    for path in directory.glob("**/*.*"):  # files only (not dirs)
        strpath = str(path)
        if not strpath.endswith(exts):
            continue
        # print(f"  - {strpath[len(str(directory)):]}")
        with open(path, "r", encoding="utf-8") as src:
            content = src.read()
        replaced = content.replace(text, replace)
        if content != replaced:
            print(f"  - {strpath[len(str(directory)):]}")
        with open(path, "w", encoding="utf-8") as dest:
            dest.write(replaced)


def _command():
    # http://argh.readthedocs.org/en/latest/
    parser = ArghParser(description=replace_many.__doc__)
    parser.set_default_command(replace_many)
    parser.dispatch()


if __name__ == "__main__":
    _command()
