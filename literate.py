import sys
import re
import argparse

# General
## Prevents a crash from occuring
def errorCheckFile(filename):
    # Error Checking
    try:
        doc = open(filename, "r")
    except IOError:
        print("ERROR could not find ", filename)
        raise SystemExit


# String Preperation
## A label has no white spaces and is all lowercase
def labelReady(line):
    line1 = "".join(line.split())
    line2 = line1.lower()
    return line2


## Anchor links are all lowercase, and use hypen for spaces, and no *
def anchorReady(line):
    line = line.replace("#", " ")   # remove header level
    line = line.strip()             # remove trailing
    line = line.replace(" ", "-")   # space to hypen
    line = line.replace("*", "")    # Remove italics/bold and whatever else
    line = line.lower()             # lowercase
    return line


## Removes the # from a header
def headerLinkReady(line):
    level = findHeader(line)
    line1 = line[level + 1 :]
    return line1


# Literate Finding Functions
## Finds if the name of the file being called for inclusion
def findFileInclude(line):
    line = labelReady(line)
    x = re.search("@include{.*}", line)
    if x:
        found = x.group()
        return found[8:-1]
    else:
        return -1


# Finds if a line starts with a @.
## This is a startline comment
### @
def findLitStatement(line):
    line = labelReady(line)
    x = re.search("^@", line)  # Starts with a @ is a lit statement
    if x:
        return True
    else:
        return False


## Removes a inline comment
### unlike the other find functions it only returns a line without a comment, even if one was not originally present
### @comment{.*}
def findLitComment(line):
    x = re.search("@comment{.*}", line)
    if x:
        found = x.group()
        newline = line.replace(found, "")
        return newline
    else:
        return line


## Finds lit comment type
### Unlike a comment type is the type of comment a code type has.
### @commentsyntax{.*}
def findCommentType(line):
    line = labelReady(line)
    x = re.search("@syntax{.*}", line)
    if x:
        found = x.group()
        return found[8:-1]
    else:
        return -1

## Returns the code type
### @code{.*}
def findLitCode(line):
    line = labelReady(line)
    x = re.search("@code{.*}", line)
    if x:
        found = x.group()
        return found[6:-1]
    else:
        return -1


## Finds the label name of a codeblock (called block here)
### @block{.*}
def findCodeblockName(line):
    line = labelReady(line)
    x = re.search("@block{.*}", line)
    if x:
        found = x.group()
        return labelReady(found[7:-1])
    else:
        return -1


# Finds the label of a fileblock
### @file{.*}
def findFileblockName(line):
    line = labelReady(line)
    x = re.search("@file{.*}", line)
    if x:
        found = x.group()
        return found[6:-1]
    else:
        return -1


# Finds the name of a label being called
## @call{.*}
def findBlockCall(line):
    x = re.search("@call{.*}", line)
    if x:
        found = x.group()
        return (x.span()[0], labelReady(found[6:-1]))
    else:
        return (-1, "")


# Weaving the code together
## Reads a literate file. Processes all lit statements
### Doesn not handle calls!
def readLit(fileBlocks, codeBlocks, filename):
    isBlock = False
    isCode = False
    isFile = False
    block = ""
    label = ""
    commentType = ""

    doc = open(filename, "r")

    for line in doc:
        # Checking for file inclusions
        newFile = findFileInclude(line)
        if newFile != -1:
            # Do this function recursively until we dont have anymore includes
            # TODO: Im not sure what to do about two files each including each other.
                # not sure what will happen
            (fileBlocks, codeBlocks) = readLit(fileBlocks, codeBlocks, newFile)

        # Checking for comment type
        ctype=findCommentType(line)
        if ctype != -1:
            commentType = ctype

        # Checking for codeblock inclusions
        codeLabel = findCodeblockName(line)
        if codeLabel != -1:
            isCode = True
            isFile = False  # Dont think i need it but keeping
            label = codeLabel
            continue
        # Checking for fileblock inclusions
        fileLabel = findFileblockName(line)
        if fileLabel != -1:
            isCode = False  #Dont think I need, but keeping
            isFile = True
            label = fileLabel
            continue

        # If it is actually the code
        if labelReady(line).startswith("~~~"):
            # If its is the ending ~~~
            if isBlock:
                isBlock = False
                if isFile:
                    fileBlocks[label] = block
                if isCode:
                    codeBlocks[label] = block
                isFile = False
                isCode = False
                block = ""

            # If it is the first starting ~~~
            else:
                isBlock = True

                # If we have no label then just make it null
                if label == "":
                    label = "__null__"
            continue #Dont save ~~~

        # Saving to block
        if isBlock:
            block += line
        else:
            if (isCode) or (isFile):
                if commentType != "":
                    block += commentType + " " + line

    doc.close()

    return (fileBlocks, codeBlocks)


## Processes a fileblock. Adds all its calls
def runFileBlock(fileBlock, codeBlocks):
    output = ""
    for line in fileBlock.split("\n"):
        # Checking to see if there is an include block
        (indent, label) = findBlockCall(line)
        if indent != -1:
            try:
                output += runCodeBlock(label, codeBlocks, indent)
            except KeyError:
                # Block does not exist. Instead of error just add blank line
                output += "\n"
        else:
            output += line + "\n"
    return output


## Processes a codeblock. Adds all its calls
def runCodeBlock(codeLabel, codeBlocks, curIndent):
    output = ""
    for line in codeBlocks[codeLabel].split("\n"):
        if line == "":
            # This is an empty line, no spaces, no enter just empty
            continue
        (indent, label) = findBlockCall(line)
        if indent != -1:
            try:
                # Runs recursively
                # TODO: Deal with what happens if a code block calls the code block that called it.
                output += runCodeBlock(label, codeBlocks, curIndent + indent)
            except KeyError:
                # Block does not exist. Instead of error just add blank line
                output += "\n"
        else:
            output += " " * curIndent + line + "\n"

    return output


# Creating The Markdown
## Finds the level of the markdown header
### "### name" is level 3 cause it has 3 "#"
def findHeader(line):
    line = labelReady(line)
    x = re.search("^#", line)
    if x:
        return line.count("#")
    else:
        return -1


## Generates the markdown
def runDocument(filename):
    hLevel = 0
    isBlock = False
    markdown = ""
    language = ""
    toc = "# Table of Contents  \n\n"
    headers = ""

    doc = open(filename, "r")

    for line in doc:
        # Programming Language
        codeType = findLitCode(line)
        if codeType != -1:
            language = codeType
            continue

        # Markdown HeaderLevel
        level = findHeader(line)
        if level != -1:
            hLevel = level
            if isBlock == False:
                headers += line

        # Check if there is a code/file block
        label = ""
        codeLabel = findCodeblockName(line)
        fileLabel = findFileblockName(line)
        if codeLabel != -1:
            label = "*CODE " + codeLabel + "*"
        if fileLabel != -1:
            label = "*FILE " + fileLabel + "*"
        # For anchor links
        if label != "":
            blockHeader = "#" * (hLevel + 1) + " " + label + "\n"
            headers += blockHeader
            markdown += "> " + blockHeader
            continue

        # If it is actually the code
        if labelReady(line).startswith("~~~"):
            # If its is the ending ~~~
            if isBlock:
                isBlock = False
                markdown += "~~~ \n"
            else:
                isBlock = True
                markdown += "~~~ " + language + "\n"
            continue

        # Comments
        line = findLitComment(line)
        if isBlock == False:
            if findLitStatement(line):
               continue

        markdown += line

    # Table of contents
    for line in headers.split("\n"):
        if line == "":
            continue
        headerLinkReady(line)
        tocSpot = (
            " " * (2 * findHeader(line) - 1)
            + "- ["
            + headerLinkReady(line)
            + "](#"
            + anchorReady(line)
            + ")\n"
        )
        toc += tocSpot

    output = toc + "\n\n" + markdown
    return output


if __name__ == "__main__":
    __VERSION__ = "1.0.0"
    parser = argparse.ArgumentParser(description="Literate programming tool", allow_abbrev=False)
    parser.add_argument("filenames", nargs="*", help="The base literate filename")
    parser.add_argument("--version", action="version", version=__VERSION__)
    parser.add_argument("--verbose", action="store_true", help="Make verbose")
    parser.add_argument("--markdown", nargs=1, help="Save markdown to this directory")
    parser.add_argument(
        "--dry-run", action="store_false", help="Print code and markdown to std out"
    )
    parser.add_argument("--no-doc", action="store_false", help="Do not make documentation")
    parser.add_argument("--no-code", action="store_false", help="Do not make code")
    args = parser.parse_args()

    # Arguments
    litFiles = args.filenames
    markdownDir = args.markdown
    isVerbose = args.verbose
    isSave = args.dry_run
    isDoc = args.no_doc
    isCode = args.no_code

    # Reading the literate files
    fileblocks = {}
    codeblocks = {}
    for litFile in litFiles:
        # This makes sures the file at least exists
        errorCheckFile(litFile)
        # Reading file
        fileblocks, codeblocks = readLit(fileblocks, codeblocks, litFile)

    # Making the code
    if isCode:
        for filename in fileblocks:
            # output is the code
            output = runFileBlock(fileblocks[filename], codeblocks)

            # Printing the code if Verbose
            if isVerbose:
                print(filename)
                print(output)
                print()

            # Saving code
            if isSave:
                code = open(filename, "w")
                code.write(output)
                code.close()

    # Making the documentation
    if isDoc:
        for litFile in litFiles:
            markdown = runDocument(litFile)
            saveName = litFile.split(".", 1)[0] + ".md"

            # Printing the code if Verbose
            if isVerbose:
                print(saveName)
                print(markdown)
                print()

            # Saving code
            if isSave:
                mark = ""
                try:
                    mark = open(markdownDir[0] + "/" + saveName, "w")
                except TypeError:
                    mark = open(saveName, "w")
                mark.write(markdown)
                mark.close()
