import argparse
import re
import os
from typing import List, Dict
from subprocess import call


class Block:
    """
    Represents a generic block of content.

    Attributes:
        content (str): The content of the block.
        container (str): The name of the container file without extension.
    """

    def __init__(self, content: str, container: str) -> None:
        self.content = content
        self.container = os.path.basename(container).rsplit(".", 1)[0]


class FileBlock(Block):
    """
    Represents a file block, inheriting from Block.

    Attributes:
        language (str): The programming language of the file.
        location (str): The location of the file.
        name (str): The name of the file without extension.
        calling (List[str]): List of blocks this file block is calling.
        called_by (List[str]): List of blocks calling this file block.
        type (str): The type of block, set to "file".
        calling_name (str): The name used for calling.
    """

    def __init__(self, content: str, container: str, language: str, name: str) -> None:
        super().__init__(content, container)
        self.language = language
        self.location = name
        self.name = os.path.basename(name).rsplit(".", 1)[0]
        self.calling: List[str] = []
        self.called_by: List[str] = []
        self.type = "file"
        self.calling_name = ""


class CodeBlock(FileBlock):
    """
    Represents a code block, inheriting from FileBlock.

    Attributes:
        type (str): The type of block, set to "code".
    """

    def __init__(self, content: str, container: str, language: str, name: str) -> None:
        super().__init__(content, container, language, name)
        self.type = "code"


class DocumentationBlock(Block):
    """
    Represents a documentation block, inheriting from Block.

    Attributes:
        type (str): The type of block, set to "doc".
    """

    def __init__(self, content: str, container: str) -> None:
        super().__init__(content, container)
        self.type = "doc"


class Container:
    """
    Represents a container for blocks.

    Attributes:
        blocks (List[Block]): List of blocks in the container.
        name (str): The name of the container file without extension.
        code_dir (str): Directory for code files.
        doc_dir (str): Directory for documentation files.
        title (str): Title of the container.
        execute (List[str]): List of execution commands.
    """

    def __init__(self, name: str) -> None:
        self.blocks: List[Block] = []
        self.name = os.path.basename(name).rsplit(".", 1)[0]
        self.code_dir = ""
        self.doc_dir = ""
        self.title = ""
        self.execute = []  # VERY DANGEROUS
        self.local_link = []
        self.web_link = []  # VERY DANGEROUS
        self.local_script = []
        self.web_script = []  # VERY DANGEROUS

    def add(self, block: Block) -> None:
        """
        Adds a block to the container.

        Args:
            block (Block): The block to add.
        """
        self.blocks.append(block)

    def set_title(self, title: str) -> None:
        """
        Sets the title of the container.

        Args:
            title (str): The title to set.
        """
        self.title = title

    def add_llink(self, link_type: str, link_address: str) -> None:
        self.local_link.append([link_type, link_address])

    def add_wlink(self, link_type: str, link_address: str) -> None:
        self.web_link.append([link_type, link_address])


def make_block(
    block_type: str, content: str, container: str, language: str = "", name: str = ""
) -> Block:
    """
    Creates a block based on the type.

    Args:
        block_type (str): The type of block ("doc", "file", "code").
        content (str): The content of the block.
        container (str): The container file name.
        language (str, optional): The programming language of the block. Defaults to "".
        name (str, optional): The name of the block. Defaults to "".

    Returns:
        Block: The created block.
    """
    content = content.rstrip("\n")  # remove the last "\n"
    if block_type == "doc":
        return DocumentationBlock(content, container)
    elif block_type == "file":
        return FileBlock(content, container, language, name)
    elif block_type == "code":
        return CodeBlock(content, container, language, name)
    else:
        raise ValueError(f"Unknown block type: {block_type}")


def parse_files(filenames: List[str]) -> Dict[str, Container]:
    """
    Parses files and creates containers with blocks.

    Args:
        filenames (List[str]): List of filenames to parse.

    Returns:
        Dict[str, Container]: Dictionary of containers.
    """

    def extract_last_match(pattern: str, content: str) -> str:
        matches = re.findall(pattern, content)
        return matches[-1] if matches else ""

    containers: Dict[str, Container] = {}
    pattern1 = r"```([\w_]+) ([\w_.-]+)\s*"  # Code and file block starting
    pattern2 = r"```\s*"  # Code and file block ending

    for filename in filenames:
        container = Container(filename)
        with open(filename, "r") as file:
            text = file.read()

        container.title = extract_last_match(r"@title{(.*?)}", text)
        container.doc_dir = extract_last_match(r"@documentation_folder{(.*?)}", text)
        container.code_dir = extract_last_match(r"@code_folder{(.*?)}", text)
        container.execute = re.findall(r"@execute_end{(.*?)}", text)
        container.local_script = re.findall(r"@local_script{(.*?)}", text)
        container.web_script = re.findall(r"@web_script{(.*?)}", text)  # dangerous
        links = re.findall(r"@local_link{(.*?)}", text)
        if links:
            for link in links:
                link = link.split()
                container.add_llink(link[0], link[1])
        links = re.findall(r"@web_link{(.*?)}", text)
        if links:
            for link in links:
                link = link.split()
                container.add_wlink(link[0], link[1])

        content, language, name = "", "", ""
        block_type = "doc"  # Doc is the default.
        for line in text.split("\n"):
            start_match = re.match(pattern1, line)
            end_match = re.match(pattern2, line)
            if start_match:
                if content:
                    container.add(
                        make_block(block_type, content, filename, language, name)
                    )
                content, language, name = "", "", ""  # Reset
                language = start_match.group(1).strip()
                name = start_match.group(2).strip()
                block_type = "file" if re.search(r"\.\w+$", name) else "code"
            elif end_match:
                if block_type in {"file", "code"} and content:
                    container.add(
                        make_block(block_type, content, filename, language, name)
                    )
                content, language, name = "", "", ""  # Reset
                block_type = "doc"
            else:
                content += line + "\n"

        if content:
            container.add(make_block(block_type, content, filename, language, name))
        containers[container.name] = container

    return containers


def replace_calls(
    content: str, code_blocks: Dict[str, CodeBlock], index: int = 0, max_index: int = 12
) -> str:
    """
    Replaces @call{} patterns in the content with the corresponding code blocks.

    Args:
        content (str): The content with @call{} patterns.
        code_blocks (Dict[str, CodeBlock]): Dictionary of code blocks.
        index (int, optional): Current recursion index. Defaults to 0.
        max_index (int, optional): Maximum recursion depth. Defaults to 12.

    Returns:
        str: The content with @call{} patterns replaced.
    """

    def add_indent(block_content: str, indent_level: int) -> str:
        lines = block_content.split("\n")
        spaces = " " * (indent_level - 1)
        indented_lines = [lines[0]] + [spaces + line for line in lines[1:]]
        return "\n".join(indented_lines)

    lines = content.split("\n")
    updated_lines = []

    for line in lines:
        indent_level = len(line) - len(line.lstrip())
        updated_line = line

        # Find all @call{} patterns in the line
        calls = re.findall(r"@call{(.*?)}", line)
        for call in calls:
            stripped_call = call.strip()  # removing trailing spaces
            if stripped_call in code_blocks:
                indented_block = add_indent(
                    code_blocks[stripped_call].content, indent_level + 1
                )
                updated_line = updated_line.replace(f"@call{{{call}}}", indented_block)
            else:
                print(f"ERROR: callblock not found: {call}")
                updated_line = updated_line.replace(
                    f"@call{{{call}}}", f"@error{{{call}}}"
                )

        updated_lines.append(updated_line)

    block_text = "\n".join(updated_lines)

    # Check for remaining @call{...} patterns
    if (max_index == -1 or index < max_index) and re.search(r"@call{.*?}", block_text):
        return replace_calls(block_text, code_blocks, index + 1, max_index)

    return block_text


def find_calls(
    container_dict: Dict[str, Container], blocks: Dict[str, Block]
) -> Dict[str, Block]:
    # Split into code and file blocks
    for block in blocks.values():
        block.calling_name = (
            os.path.join(
                container_dict[block.container].doc_dir, block.container + ".html"
            )
            + "#"
            + block.type
            + "::"
            + block.name
        )
        lines = block.content.split("\n")
        for line in lines:
            calls = re.findall(r"@call\{(.*?)\}", line)
            for call in calls:
                stripped_call = call.strip()
                try:
                    calling_block = blocks[stripped_call]
                except KeyError:
                    continue
                calling_block_name = (
                    os.path.join(
                        container_dict[calling_block.container].doc_dir,
                        calling_block.container + ".html",
                    )
                    + "#code::"
                    + calling_block.name
                )
                calling_block.called_by.append(block.calling_name)
                block.calling.append(calling_block_name)
                blocks[stripped_call] = calling_block
        blocks[block.name] = block
    return blocks


def write_html(containers: Dict[str, Container], blocks: Dict[str, Block]) -> None:
    def href_to_html(hrefs, label, current_dir):
        current_dir = "/".join([".."] * (len(current_dir.split("/")) - 1)) + "/"
        html_refs = []
        for link in hrefs:
            display_text = link.split("::")[-1]
            html_ref = f'<a href="{current_dir+link}">{display_text}</a>'
            html_refs.append(html_ref)
        return f'<p><b>{label}: {", ".join(html_refs)}</b></p>'

    def local_link_to_html(links, current_dir):
        current_dir = "/".join([".."] * (len(current_dir.split("/")) - 1)) + "/"
        html_links = []
        for link in links:
            link_type = link[0]
            link_add = link[1]
            link_text = f'<link rel="{link_type}" href="{current_dir+link_add}">'
            html_links.append(link_text)
        return f"{"\n".join(html_links)}"

    def web_link_to_html(links):
        html_links = []
        for link in links:
            link_type = link[0]
            link_add = link[1]
            link_text = f'<link rel="{link_type}" href="{link_add}">'
            html_links.append(link_text)
        return f"{"\n".join(html_links)}"

    def local_script_to_html(scripts, current_dir):
        current_dir = "/".join([".."] * (len(current_dir.split("/")) - 1)) + "/"
        html_scripts = []
        for script in scripts:
            link_text = f'<script src="{current_dir+script}"></script>'
            html_scripts.append(link_text)
        return f"{"\n".join(html_scripts)}"

    def web_script_to_html(scripts):
        html_scripts = []
        for script in scripts:
            link_text = f'<script src="{script}"></script>'
            html_scripts.append(link_text)
        return f"{"\n".join(html_scripts)}"

    for container in containers.values():
        doc_filename = os.path.join(container.doc_dir, container.name + ".html")
        doc_title = container.title
        llinks = local_link_to_html(container.local_link, container.doc_dir)
        wlinks = web_link_to_html(container.web_link)
        lscripts = local_script_to_html(container.local_script, container.doc_dir)
        wscripts = web_script_to_html(container.web_script)
        head = f"""
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{doc_title}</title>
{wscripts}
{lscripts}
{wlinks}
{llinks}
</head>
"""
        html_content = ""
        for block in container.blocks:
            if block.type == "doc":
                patterns = [
                    (r"###### (.*)", r"<h6>\1</h6>"),
                    (r"##### (.*)", r"<h5>\1</h5>"),
                    (r"#### (.*)", r"<h4>\1</h4>"),
                    (r"### (.*)", r"<h3>\1</h3>"),
                    (r"## (.*)", r"<h2>\1</h2>"),
                    (r"# (.*)", r"<h1>\1</h1>"),
                    (r"\*\*(.*?)\*\*", r"<b>\1</b>", re.DOTALL),
                    (r"__(.*?)__", r"<b>\1</b>", re.DOTALL),
                    (r"\*(.*?)\*", r"<i>\1</i>", re.DOTALL),
                    (r"_(.*?)_", r"<i>\1</i>", re.DOTALL),
                ]
                for pattern, replacement, *flags in patterns:
                    if flags:
                        block.content = re.sub(
                            pattern, replacement, block.content, flags=flags[0]
                        )
                    else:
                        block.content = re.sub(pattern, replacement, block.content)
                block.content = re.sub(
                    r"@\w+\{[^}]*\}", "", block.content
                )  # remove commands
                html_content += "<p>" + block.content + "\n</p>"
            if block.type in ["file", "code"]:
                code_name = f"{block.type}::{block.name}"
                current_name = f'<p class="{block.type}block">{block.name}</p>'
                calling = href_to_html(block.calling, "Calling", container.doc_dir)
                called_by = href_to_html(
                    block.called_by, "Called by", container.doc_dir
                )
                content = f"""{current_name}{calling}{called_by}
<pre><code id="{code_name}" class="{block.language}">{block.content}</pre></code>"""
                html_content += content + "\n"
        html = f"""<!DOCTYPE html>
<html>
{head}
<body>
{html_content}
</body>
</html>"""

        # Writing
        if not os.path.exists(container.doc_dir) and container.doc_dir:
            os.makedirs(container.doc_dir)
        with open(doc_filename, "w") as file:
            file.write(html)


def main(filenames=[]):
    containers = parse_files(filenames)

    # Split into code and file blocks
    code_blocks = {}
    file_blocks = {}
    for container in containers.values():
        for block in container.blocks:
            if block.type == "file":
                file_blocks[block.name] = block
            elif block.type == "code":
                code_blocks[block.name] = block

    # Writing Code
    for block in file_blocks.keys():
        output = replace_calls(file_blocks[block].content, code_blocks, 0)
        container = containers[file_blocks[block].container]
        if not os.path.exists(container.code_dir) and container.code_dir:
            os.makedirs(container.code_dir)
        with open(container.code_dir + file_blocks[block].location, "w") as file:
            file.write(output)

    # Writing Documentations
    blocks_dict = {**file_blocks, **code_blocks}
    blocks_dict = find_calls(containers, blocks_dict)
    write_html(containers, blocks_dict)

    # Running Executions
    for container in containers.values():
        for command in container.execute:
            call(command.split())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Converts Markdown code to python and html code"
    )
    parser.add_argument("--files", nargs="+", help="List of file names", required=True)
    args = parser.parse_args()
    filenames = args.files
    main(filenames)
