#!/usr/bin/env python3
"""
Test script that will actually test the expected behavior vs buggy implementation
"""

import sys
from buggy_code import divide, calculate_average, get_first_element, safe_int_conversion

def test_functions():
    """Test functions against expected behavior"""
    
    print("🧪 Testing functions for correct behavior...")
    failed_tests = []
    
    # Test 1: Division by zero should raise ZeroDivisionError
    print("\n1. Testing division by zero...")
    try:
        result = divide(10, 0)
        if result == 0:
            print(f"❌ BUG: divide(10, 0) returned {result}, should raise ZeroDivisionError")
            failed_tests.append("divide(10, 0) should raise ZeroDivisionError, not return 0")
        else:
            print(f"❌ BUG: divide(10, 0) returned {result}, should raise ZeroDivisionError")
            failed_tests.append(f"divide(10, 0) should raise ZeroDivisionError, not return {result}")
    except ZeroDivisionError:
        print("✅ divide(10, 0) correctly raised ZeroDivisionError")
    except Exception as e:
        print(f"❌ BUG: divide(10, 0) raised unexpected error: {e}")
        failed_tests.append(f"divide(10, 0) raised {type(e).__name__} instead of ZeroDivisionError")
    
    # Test 2: Empty list average should raise ZeroDivisionError
    print("\n2. Testing empty list average...")
    try:
        result = calculate_average([])
        if result == 0:
            print(f"❌ BUG: calculate_average([]) returned {result}, should raise ZeroDivisionError")
            failed_tests.append("calculate_average([]) should raise ZeroDivisionError, not return 0")
        else:
            print(f"❌ BUG: calculate_average([]) returned {result}, should raise ZeroDivisionError")
            failed_tests.append(f"calculate_average([]) should raise ZeroDivisionError, not return {result}")
    except ZeroDivisionError:
        print("✅ calculate_average([]) correctly raised ZeroDivisionError")
    except Exception as e:
        print(f"❌ BUG: calculate_average([]) raised unexpected error: {e}")
        failed_tests.append(f"calculate_average([]) raised {type(e).__name__} instead of ZeroDivisionError")
    
    # Test 3: Empty list first element should raise IndexError
    print("\n3. Testing empty list first element...")
    try:
        result = get_first_element([])
        if result is None:
            print(f"❌ BUG: get_first_element([]) returned {result}, should raise IndexError")
            failed_tests.append("get_first_element([]) should raise IndexError, not return None")
        else:
            print(f"❌ BUG: get_first_element([]) returned {result}, should raise IndexError")
            failed_tests.append(f"get_first_element([]) should raise IndexError, not return {result}")
    except IndexError:
        print("✅ get_first_element([]) correctly raised IndexError")
    except Exception as e:
        print(f"❌ BUG: get_first_element([]) raised unexpected error: {e}")
        failed_tests.append(f"get_first_element([]) raised {type(e).__name__} instead of IndexError")
    
    # Test 4: Invalid string conversion should raise ValueError
    print("\n4. Testing invalid string conversion...")
    try:
        result = safe_int_conversion("abc")
        if result == 0:
            print(f"❌ BUG: safe_int_conversion('abc') returned {result}, should raise ValueError")
            failed_tests.append("safe_int_conversion('abc') should raise ValueError, not return 0")
        else:
            print(f"❌ BUG: safe_int_conversion('abc') returned {result}, should raise ValueError")
            failed_tests.append(f"safe_int_conversion('abc') should raise ValueError, not return {result}")
    except ValueError:
        print("✅ safe_int_conversion('abc') correctly raised ValueError")
    except Exception as e:
        print(f"❌ BUG: safe_int_conversion('abc') raised unexpected error: {e}")
        failed_tests.append(f"safe_int_conversion('abc') raised {type(e).__name__} instead of ValueError")
    
    # Test normal cases too
    print("\n5. Testing normal cases...")
    try:
        assert divide(10, 2) == 5, "divide(10, 2) should return 5"
        assert calculate_average([1, 2, 3, 4, 5]) == 3, "calculate_average([1,2,3,4,5]) should return 3"
        assert get_first_element([1, 2, 3]) == 1, "get_first_element([1,2,3]) should return 1"
        assert safe_int_conversion("123") == 123, "safe_int_conversion('123') should return 123"
        print("✅ All normal cases work correctly")
    except AssertionError as e:
        print(f"❌ Normal case failed: {e}")
        failed_tests.append(str(e))
    
    if failed_tests:
        print(f"\n💥 {len(failed_tests)} test(s) failed:")
        for i, failure in enumerate(failed_tests, 1):
            print(f"  {i}. {failure}")
        return False
    else:
        print("\n🎉 All tests passed - functions are properly implemented!")
        return True

if __name__ == "__main__":
    success = test_functions()
    sys.exit(0 if success else 1)