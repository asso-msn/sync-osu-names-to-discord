"""Generate the config variables table in README.md.

Reads config.py, extracts Config class fields and their preceding comment
blocks, then replaces the content between the MARK and ENDMARK tags in
README.md with a Markdown table.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.py"
README_PATH = ROOT / "README.md"

MARK = "<!-- MARK: Config vars -->"
ENDMARK = "<!-- ENDMARK -->"


def get_fields():
    source = CONFIG_PATH.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)

    config_class = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "Config"
    )

    fields = []
    for stmt in config_class.body:
        if not isinstance(stmt, ast.AnnAssign):
            continue

        name = stmt.target.id
        type_str = ast.unparse(stmt.annotation)
        default = ast.unparse(stmt.value) if stmt.value is not None else None

        # Collect contiguous comment lines directly above this statement
        comment_lines = []
        i = stmt.lineno - 2  # convert to 0-indexed, then go one line up
        while i >= 0 and lines[i].strip().startswith("#"):
            comment_lines.insert(0, lines[i].strip().lstrip("#").strip())
            i -= 1
        comment = " ".join(comment_lines)

        fields.append(
            {
                "name": name,
                "type": type_str,
                "default": default,
                "comment": comment,
            }
        )

    return fields


def generate_markdown(fields):
    rows = [
        "| Variable | Type | Default | Description |",
        "| --- | --- | --- | --- |",
    ]
    for f in fields:
        default = (
            f"`{f['default']}`" if f["default"] is not None else "*(required)*"
        )
        type_str = f["type"].replace("|", r"\|")
        rows.append(
            f"| `{f['name']}` | `{type_str}` | {default} | {f['comment']} |"
        )
    return "\n".join(rows)


def update_readme(markdown):
    content = README_PATH.read_text()

    mark_idx = content.find(MARK)
    endmark_idx = content.find(ENDMARK)

    if mark_idx == -1 or endmark_idx == -1:
        raise ValueError("MARK or ENDMARK not found in README.md")

    after_mark = mark_idx + len(MARK)
    README_PATH.write_text(
        content[:after_mark]
        + "\n\n"
        + markdown
        + "\n\n"
        + content[endmark_idx:]
    )


if __name__ == "__main__":
    fields = get_fields()
    markdown = generate_markdown(fields)
    update_readme(markdown)
    print("README.md updated.")
