"""
Unit tests for new functionality.
These test the latest features being developed.
"""
import pytest
import sys
sys.path.insert(0, 'src')

from calculator import add, subtract, multiply, divide, percentage


class TestAddition:
    """Tests for add function."""
    
    def test_add_positive_numbers(self):
        assert add(2, 3) == 5
    
    def test_add_negative_numbers(self):
        assert add(-1, -1) == -2
    
    def test_add_mixed_numbers(self):
        assert add(-1, 5) == 4


class TestSubtraction:
    """Tests for subtract function."""
    
    def test_subtract_positive_numbers(self):
        assert subtract(5, 3) == 2
    
    def test_subtract_negative_result(self):
        assert subtract(3, 5) == -2


class TestMultiplication:
    """Tests for multiply function."""
    
    def test_multiply_positive_numbers(self):
        assert multiply(3, 4) == 12
    
    def test_multiply_by_zero(self):
        assert multiply(5, 0) == 0


class TestDivision:
    """Tests for divide function."""
    
    def test_divide_even(self):
        assert divide(10, 2) == 5
    
    def test_divide_decimal_result(self):
        assert divide(7, 2) == 3.5
    
    def test_divide_by_zero_raises_error(self):
        with pytest.raises(ValueError):
            divide(10, 0)


class TestPercentage:
    """Tests for percentage function."""
    
    def test_percentage_basic(self):
        assert percentage(25, 100) == 25
    
    def test_percentage_half(self):
        assert percentage(50, 200) == 25
