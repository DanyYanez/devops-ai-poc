"""
Simple calculator module for PoC demonstration.
This represents your application code.
"""

def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def percentage(value, total):
    """Calculate percentage of value from total."""
    if total == 0:
        raise ValueError("Total cannot be zero")
    return (value / total) * 100
