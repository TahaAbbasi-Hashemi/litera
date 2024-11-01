@local_link{stylesheet share/default.css} <!-- If you want to attach your own CSS documents / -->
@web_link{stylesheet https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.0.3/styles/default.min.css} <!-- Incase you want colorcoded code/file blocks -->
@web_script{https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.0.3/highlight.min.js} <!-- to help with color coding fileblocks / -->
@local_script{share/color_code.js} <!-- to help with color coding fileblocks / -->

<!-- With scripts and links the order does matter. -->

@documentation_folder{docs/html/} <!-- Note, folders must end with a /  -->
@code_folder{code/} <!-- Note, folders must end with a / -->
@execute_end{python3 code/main.py}
@title{titlename}

# Heading1Name

## Heading2name

### Heading3name

#### Heading4name

##### Heading5name

###### Heading6name

This supports _italic_ text, **bold** text, and **_italic and bold_** text.
But do note, it does support all of these over multiple lines.
For instance \*this will be italic text,

and this will be italic\* That multiline opperation may or may not be accepted in your markdown viewer.

# Example Calculator Program

<!-- This is a comment, you wont see this on the HTML  -->

This program provides basic arithmetic operations: addition, subtraction, and multiplication. It is designed to demonstrate how to structure a simple calculator using Python functions and how to call these functions from a main script.

```python calculator.py
# calculator.py

@call{addition}

@call{subtraction}

@call{multiplication}
```

## Functions

Purpose: Adds two numbers.

Parameters:

a (int or float): The first number.
b (int or float): The second number.
Returns: The sum of a and b.

```python addition
def add(a, b):
    return a + b
```

Purpose: Subtracts the second number from the first number.

Parameters:

a (int or float): The number to be subtracted from.
b (int or float): The number to subtract.
Returns: The difference between a and b.

```python subtraction
def subtract(a, b):
    return a - b
```

Purpose: Multiplies two numbers.

Parameters:

a (int or float): The first number.
b (int or float): The second number.
Returns: The product of a and b.

```python multiplication
def multiply(a, b):
    return a * b
```

## Example Usage

```python main.py
# main.py

from calculator import add, subtract, multiply

def main():
    num1 = 10
    num2 = 5

    print(f"{num1} + {num2} = {add(num1, num2)}")
    print(f"{num1} - {num2} = {subtract(num1, num2)}")
    print(f"{num1} * {num2} = {multiply(num1, num2)}")

if __name__ == "__main__":
    @call{main}
```

This is just to showcase how indentation works with the calling command

```python main
main()
```
