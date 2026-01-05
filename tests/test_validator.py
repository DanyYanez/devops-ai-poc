"""
Tests for validator module.
"""
import pytest
import sys
sys.path.insert(0, 'src')

from validator import validate_email, validate_age, validate_username


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("user@example.com") == True
    
    def test_invalid_email_no_at(self):
        assert validate_email("userexample.com") == False
    
    def test_invalid_email_no_dot(self):
        assert validate_email("user@examplecom") == False
    
    def test_empty_email(self):
        assert validate_email("") == False


class TestValidateAge:
    def test_valid_age(self):
        assert validate_age(25) == True
    
    def test_zero_age(self):
        assert validate_age(0) == True
    
    def test_negative_age(self):
        assert validate_age(-1) == False
    
    def test_too_old(self):
        assert validate_age(151) == False
    
    def test_string_age(self):
        assert validate_age("25") == False


class TestValidateUsername:
    def test_valid_username(self):
        assert validate_username("john123") == True
    
    def test_too_short(self):
        assert validate_username("ab") == False
    
    def test_too_long(self):
        assert validate_username("a" * 21) == False
    
    def test_special_chars(self):
        assert validate_username("john@123") == False
    
    def test_empty_username(self):
        assert validate_username("") == False