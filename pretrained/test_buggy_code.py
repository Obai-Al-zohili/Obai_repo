import pytest
from buggy_code import divide, calculate_average, get_first_element, safe_int_conversion

def test_divide():
    """Test the divide function"""
    # Test normal division
    assert divide(10, 2) == 5
    assert divide(15, 3) == 5
    
    # Test division by zero - should not raise exception
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_calculate_average():
    """Test the calculate_average function"""
    # Test normal case
    assert calculate_average([1, 2, 3, 4, 5]) == 3
    
    # Test empty list - should not raise exception
    with pytest.raises(ZeroDivisionError):
        calculate_average([])

def test_get_first_element():
    """Test the get_first_element function"""
    # Test normal case
    assert get_first_element([1, 2, 3]) == 1
    
    # Test empty list - should not raise exception
    with pytest.raises(IndexError):
        get_first_element([])

def test_safe_int_conversion():
    """Test the safe_int_conversion function"""
    # Test normal case
    assert safe_int_conversion("123") == 123
    
    # Test invalid string - should not raise exception
    with pytest.raises(ValueError):
        safe_int_conversion("abc")