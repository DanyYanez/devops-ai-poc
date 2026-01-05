"""
Regression tests for existing functionality.
These tests ensure that previously working features continue to work.
They represent the "stable" parts of the application.
"""
import pytest
import sys
sys.path.insert(0, 'src')

from calculator import add, subtract, multiply, divide


class TestCoreAdditionRegression:
    """Regression tests for core addition - these have been stable for months."""
    
    def test_add_integers(self):
        """REGRESSION: Basic integer addition - core functionality since v1.0"""
        assert add(1, 1) == 2
        assert add(100, 200) == 300
    
    def test_add_floats(self):
        """REGRESSION: Float addition - added in v1.1"""
        result = add(1.5, 2.5)
        assert result == 4.0
    
    def test_add_large_numbers(self):
        """REGRESSION: Large number support - fixed in v1.2"""
        assert add(1000000, 2000000) == 3000000


class TestCoreSubtractionRegression:
    """Regression tests for subtraction operations."""
    
    def test_subtract_basic(self):
        """REGRESSION: Basic subtraction - core functionality since v1.0"""
        assert subtract(10, 5) == 5
    
    def test_subtract_to_negative(self):
        """REGRESSION: Negative results - bug fix v1.3"""
        assert subtract(5, 10) == -5


class TestCoreMultiplicationRegression:
    """Regression tests for multiplication operations."""
    
    def test_multiply_basic(self):
        """REGRESSION: Basic multiplication - core functionality since v1.0"""
        assert multiply(6, 7) == 42
    
    def test_multiply_negative(self):
        """REGRESSION: Negative number multiplication - v1.1"""
        assert multiply(-3, 4) == -12
        assert multiply(-3, -4) == 12


class TestCoreDivisionRegression:
    """Regression tests for division operations."""
    
    def test_divide_basic(self):
        """REGRESSION: Basic division - core functionality since v1.0"""
        assert divide(20, 4) == 5
    
    def test_divide_zero_handling(self):
        """REGRESSION: Division by zero protection - critical fix v1.2"""
        with pytest.raises(ValueError):
            divide(5, 0)


class TestEdgeCasesRegression:
    """Regression tests for edge cases discovered in production."""
    
    def test_operations_with_zero(self):
        """REGRESSION: Zero handling across operations - v1.4 hotfix"""
        assert add(0, 0) == 0
        assert subtract(0, 0) == 0
        assert multiply(0, 100) == 0
    
    def test_floating_point_precision(self):
        """REGRESSION: Float precision - investigated in v1.5"""
        result = add(0.1, 0.2)
        assert abs(result - 0.3) < 0.0001  # Tolerance for float comparison
