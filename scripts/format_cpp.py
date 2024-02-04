# pyright: strict
import subprocess

def format_cpp(content: str) -> str:
    return subprocess.run(
        ['clang-format'],
        shell=True, check=True,
        input=content, encoding='utf-8',
        capture_output=True, text=True
    ).stdout
