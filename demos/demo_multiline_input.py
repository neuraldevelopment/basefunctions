#!/usr/bin/env python3
"""
Demo script for read_multiline_input functionality.

Shows three use cases:
1. SQL statement input (completion on semicolon)
2. Python code input (completion on balanced brackets)
3. Text input (completion on 'END' keyword)
"""

from basefunctions.cli import read_multiline_input


def is_sql_complete(buffer: str) -> bool:
    """Check if SQL statement is complete (ends with semicolon)."""
    stripped = buffer.strip()
    return bool(stripped) and stripped.endswith(";")


def is_python_complete(buffer: str) -> bool:
    """Check if Python code is complete (balanced brackets, ends with valid statement)."""
    stripped = buffer.strip()
    if not stripped:
        return False

    # Count brackets
    open_parens = stripped.count("(") - stripped.count(")")
    open_brackets = stripped.count("[") - stripped.count("]")
    open_braces = stripped.count("{") - stripped.count("}")

    # All balanced and doesn't end with backslash (line continuation)
    balanced = open_parens == 0 and open_brackets == 0 and open_braces == 0
    no_continuation = not stripped.endswith("\\")

    return balanced and no_continuation


def is_text_complete(buffer: str) -> bool:
    """Check if text input is complete (user types 'END' on a line)."""
    lines = buffer.strip().split("\n")
    return any(line.strip().upper() == "END" for line in lines)


def demo_sql_input():
    """Demo: Multi-line SQL statement input."""
    print("\n" + "=" * 60)
    print("DEMO 1: SQL Statement Input")
    print("=" * 60)
    print("Enter SQL statement (completion on semicolon)")
    print("Tip: Try entering 'SELECT' on first line, then '*', then 'FROM table;'")
    print()

    sql = read_multiline_input(
        prompt="SQL> ",
        continuation_prompt="...> ",
        is_complete=is_sql_complete,
    )

    if sql:
        print("\n✓ SQL Statement received:")
        print(f"  {sql}")
    else:
        print("\n⊘ Input cancelled (Ctrl+D or Ctrl+C)")


def demo_python_input():
    """Demo: Multi-line Python code input."""
    print("\n" + "=" * 60)
    print("DEMO 2: Python Code Input")
    print("=" * 60)
    print("Enter Python code (completion on balanced brackets)")
    print("Tip: Try entering a function definition:")
    print("  def hello():")
    print("      return 'world'")
    print()

    code = read_multiline_input(
        prompt=">>> ",
        continuation_prompt="... ",
        is_complete=is_python_complete,
    )

    if code:
        print("\n✓ Python code received:")
        for line in code.split("\n"):
            print(f"  {line}")
    else:
        print("\n⊘ Input cancelled (Ctrl+D or Ctrl+C)")


def demo_text_input():
    """Demo: Free-form text input with keyword completion."""
    print("\n" + "=" * 60)
    print("DEMO 3: Free-form Text Input")
    print("=" * 60)
    print("Enter text (completion when you type 'END' on a line)")
    print("Example:")
    print("  This is my first line")
    print("  This is my second line")
    print("  END")
    print()

    text = read_multiline_input(
        prompt=">>> ",
        continuation_prompt="... ",
        is_complete=is_text_complete,
    )

    if text:
        print("\n✓ Text received:")
        for i, line in enumerate(text.split("\n"), 1):
            print(f"  {i}: {line}")
    else:
        print("\n⊘ Input cancelled (Ctrl+D or Ctrl+C)")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("read_multiline_input() DEMO")
    print("=" * 60)

    demo_sql_input()
    demo_python_input()
    demo_text_input()

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
