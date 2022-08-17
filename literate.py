#! /usr/bin/python3

import sys


def helpMessage():
    print("literate [options] <filename.lit>")
    print("-d --dry-run to only print to stdout instead of saving to a file")
    print("-h --help show this message")
    print("-m create markdown documentation")
    print("--contents create table of contents")
    print("-v --verbose to print to stdout")
    print("-V --version for version")
    print("Filename must include .lit")
    print("Example: literate testfile.lit")
    raise SystemExit


def versionMessage():
    __version__ = "0.1.0"
    print(__version__)


def runBlock(output, label, codeBlocks, indents):
    for line in codeBlocks[label].split("\n"):
        if ("@{" in line) and ("}" in line):
            start = line.find("@{")
            end = line.find("}")
            nlabel_ = line[start + 2 : end]
            nlabel = "".join(nlabel_.split()).lower()
            indents.append(start)
            try:
                output = runBlock(output, nlabel, codeblocks, indents)
            except KeyError:  # If the block does not exist just skip it.
                output += "\n"
            indents.pop()
        else:
            currentIndent = 0
            for indent in indents:
                currentIndent += indent
            strIndent = " " * currentIndent
            strCodeLine = strIndent + line
            output += strCodeLine + "\n"
    return output

def readLit(fileBlocks, codeBlocks, filename, base):
    isBlock = False
    isCode = False
    isFile = False
    block = ""
    label = ""
    try:
        doc=open(filename, "r")
    except IOError:
        if base == True:
            print("ERROR: Bad file name, file must be labeled as .lit")
            raise SystemExit
        else:
            print("WARNING could not find ", filename)
            return (fileBlocks, codeBlocks)
    
    for line in doc:
        if "@lit_include" in line:
            newFile_=line[12:]
            newFile = "".join(newFile_.split())
            (fileBlocks, codeBlocks) = readLit(fileBlocks, codeBlocks, newFile, False)
            
        elif "---" in line:  # Start or end of a block
            if isBlock == True:  # End label
                if isFile == True:
                    fileBlocks[label] = block
                elif isCode == True:
                    codeBlocks[label] = block
                # reset
                isFile = isCode = isBlock = False
                label = block = ""

            else:
                line1 = line[3:]  # remove "---"
                label = "".join(line1.split())  # Remove all whitespaces
                if "." in line:  # We have a file
                    isFile = True
                else:
                    isCode = True
                    label = label.lower()
                isBlock = True

        elif isBlock == True:
            block += line
    doc.close()
    
    return (fileBlocks, codeBlocks)
    

if __name__ == "__main__":
    # Arguments
    baseLiteFile = 0
    isSave = True
    isPrint = False
    isCOT = False   # Table Of Contents
    for arg in sys.argv:
        if (arg == "-h") or (arg == "--help"):
            helpMessage()
        elif (arg == "-V") or (arg == "--version"):
            versionMessage()
        elif (arg == "-d") or (arg == "--dry-run"):
            isSave = False
            isPrint = True
        elif (arg == "-v") or (arg == "--verbose"):
            isPrint = True
        elif ".lit" in arg:
            baseLiteFile = arg
        elif ".py" in arg:
            continue
        else:
            helpMessage()

    # Was provided no file 
    if baseLiteFile == 0:
        raise SystemExit

    # Reading the literate files
    fileblocks = {}
    codeblocks = {}
    fileblocks, codeblocks = readLit(fileblocks, codeblocks, baseLiteFile, True)


    # Writing code
    blockIndent = []  # First in last out
    for filename in fileblocks:  # Can only write to one file at a time
        output = ""
        for line in fileblocks[filename].split("\n"):
            if ("@{" in line) and ("}" in line):
                # Get indent level!s
                start = line.find("@{")
                end = line.find("}")
                blockLabel_ = line[start + 2 : end]
                blockLabel = "".join(blockLabel_.split()).lower()
                blockIndent.append(start)
                try:
                    output = runBlock(output, blockLabel, codeblocks, blockIndent)
                except KeyError:  # If the block does not exist just skip it.
                    output += "\n"
                blockIndent.pop()
            else:
                output += line + "\n"

        if isPrint:
            print(filename)
            print(output)
            
        if isSave:
            code = open(filename, "w")
            code.write(output)
            code.close()
            
    # Writing documentation
            
