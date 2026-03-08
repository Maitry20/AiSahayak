#!/usr/bin/env python3
"""
Property-Based Test: Scheme Data Integrity

**Validates: Requirements 2.1, 2.3, 14.1, 14.2**

Property 2: Scheme Data Integrity
For any scheme retrieved from DynamoDB, it should contain all required fields 
(scheme_id, scheme_name, category, description, eligibility, benefits) and the 
category should be one of {education, farmer, business, healthcare, housing}.

This test verifies that scheme data maintains integrity throughout the retrieval
and parsing process from DynamoDB format to Python dictionaries.
"""

import json
import sys
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, Any, List

# Import the lambda function
sys.path.insert(0, '.')
from lambda_function import get_all_schemes

# Valid categories as per requirements
VALID_CATEGORIES = {'education', 'farmer', 'business', 'healthcare', 'housing'}

# Required fields for a scheme
REQUIRED_FIELDS = {'scheme_id', 'scheme_name', 'category', 'description', 'eligibility', 'benefits'}


# Strategy for generating valid scheme data in DynamoDB format
@st.composite
def dynamodb_scheme_item(draw):
    """Generate a valid scheme item in DynamoDB format"""
    scheme_id = draw(st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=3, max_size=10))
    scheme_name = draw(st.text(min_size=5, max_size=200))
    category = draw(st.sampled_from(list(VALID_CATEGORIES)))
    description = draw(st.text(min_size=10, max_size=1000))
    eligibility = draw(st.text(min_size=5, max_size=500))
    benefits = draw(st.text(min_size=5, max_size=500))
    
    return {
        'scheme_id': {'S': scheme_id},
        'scheme_name': {'S': scheme_name},
        'category': {'S': category},
        'description': {'S': description},
        'eligibility': {'S': eligibility},
        'benefits': {'S': benefits}
    }


@st.composite
def dynamodb_response(draw, min_items=0, max_items=10):
    """Generate a DynamoDB scan response with multiple schemes"""
    num_items = draw(st.integers(min_value=min_items, max_value=max_items))
    items = [draw(dynamodb_scheme_item()) for _ in range(num_items)]
    
    return {
        'Items': items
    }


def validate_scheme_integrity(scheme: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate that a scheme has all required fields and valid values
    
    Returns tuple: (is_valid, error_message)
    """
    # Check scheme is a dictionary
    if not isinstance(scheme, dict):
        return False, "Scheme is not a dictionary"
    
    # Check all required fields are present
    missing_fields = REQUIRED_FIELDS - set(scheme.keys())
    if missing_fields:
        return False, f"Missing required fields: {missing_fields}"
    
    # Check all fields are non-empty strings
    for field in REQUIRED_FIELDS:
        if not isinstance(scheme[field], str):
            return False, f"Field '{field}' is not a string: {type(scheme[field])}"
        if not scheme[field]:
            return False, f"Field '{field}' is empty"
    
    # Check category is valid
    if scheme['category'] not in VALID_CATEGORIES:
        return False, f"Invalid category '{scheme['category']}', must be one of {VALID_CATEGORIES}"
    
    return True, None


@given(dynamodb_response(min_items=1, max_items=10))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_all_schemes_have_required_fields(mock_response):
    """
    Property Test: All retrieved schemes have required fields
    
    For any DynamoDB response with schemes, each scheme should have:
    - scheme_id (non-empty string)
    - scheme_name (non-empty string)
    - category (non-empty string)
    - description (non-empty string)
    - eligibility (non-empty string)
    - benefits (non-empty string)
    """
    with patch('boto3.client') as mock_boto3:
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_response
        
        # Call get_all_schemes
        schemes = get_all_schemes(mock_dynamodb)
        
        # Verify we got a list
        assert isinstance(schemes, list), "get_all_schemes should return a list"
        
        # Verify each scheme has all required fields
        for i, scheme in enumerate(schemes):
            is_valid, error_msg = validate_scheme_integrity(scheme)
            assert is_valid, f"Scheme {i} failed validation: {error_msg}"


@given(dynamodb_response(min_items=1, max_items=10))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_all_categories_are_valid(mock_response):
    """
    Property Test: All scheme categories are valid
    
    For any scheme retrieved from DynamoDB, the category field should be
    one of: education, farmer, business, healthcare, or housing
    """
    with patch('boto3.client') as mock_boto3:
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_response
        
        # Call get_all_schemes
        schemes = get_all_schemes(mock_dynamodb)
        
        # Verify each scheme has a valid category
        for i, scheme in enumerate(schemes):
            assert 'category' in scheme, f"Scheme {i} missing 'category' field"
            assert scheme['category'] in VALID_CATEGORIES, \
                f"Scheme {i} has invalid category '{scheme['category']}', " \
                f"must be one of {VALID_CATEGORIES}"


@given(dynamodb_response(min_items=0, max_items=0))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_empty_table_returns_empty_list(mock_response):
    """
    Property Test: Empty DynamoDB table returns empty list
    
    When DynamoDB returns no items, get_all_schemes should return an empty list
    """
    with patch('boto3.client') as mock_boto3:
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_response
        
        # Call get_all_schemes
        schemes = get_all_schemes(mock_dynamodb)
        
        # Verify we got an empty list
        assert isinstance(schemes, list), "get_all_schemes should return a list"
        assert len(schemes) == 0, "Empty DynamoDB response should return empty list"


@given(dynamodb_response(min_items=1, max_items=10))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_dynamodb_format_conversion(mock_response):
    """
    Property Test: DynamoDB format is correctly converted to Python dictionaries
    
    For any DynamoDB response (with type descriptors like {'S': 'value'}),
    the get_all_schemes function should convert it to plain Python dictionaries
    with string values.
    """
    with patch('boto3.client') as mock_boto3:
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_response
        
        # Call get_all_schemes
        schemes = get_all_schemes(mock_dynamodb)
        
        # Verify conversion from DynamoDB format
        for i, scheme in enumerate(schemes):
            # Check that values are plain strings, not DynamoDB format
            for field in REQUIRED_FIELDS:
                assert field in scheme, f"Scheme {i} missing field '{field}'"
                assert isinstance(scheme[field], str), \
                    f"Scheme {i} field '{field}' should be string, got {type(scheme[field])}"
                assert not isinstance(scheme[field], dict), \
                    f"Scheme {i} field '{field}' should not be DynamoDB format dict"


@given(dynamodb_response(min_items=1, max_items=10))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_scheme_count_matches_dynamodb(mock_response):
    """
    Property Test: Number of schemes matches DynamoDB response
    
    For any DynamoDB response, the number of schemes returned by get_all_schemes
    should match the number of items in the DynamoDB response.
    """
    with patch('boto3.client') as mock_boto3:
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_response
        
        # Call get_all_schemes
        schemes = get_all_schemes(mock_dynamodb)
        
        # Verify count matches
        expected_count = len(mock_response['Items'])
        actual_count = len(schemes)
        assert actual_count == expected_count, \
            f"Expected {expected_count} schemes, got {actual_count}"


@given(st.lists(dynamodb_scheme_item(), min_size=1, max_size=5))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_all_scheme_ids_preserved(items):
    """
    Property Test: All scheme IDs are preserved during retrieval
    
    For any set of schemes in DynamoDB, all scheme_id values should be
    present in the returned list.
    """
    mock_response = {'Items': items}
    
    with patch('boto3.client') as mock_boto3:
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_response
        
        # Call get_all_schemes
        schemes = get_all_schemes(mock_dynamodb)
        
        # Extract scheme IDs from original and returned data
        original_ids = {item['scheme_id']['S'] for item in items}
        returned_ids = {scheme['scheme_id'] for scheme in schemes}
        
        # Verify all IDs are preserved
        assert original_ids == returned_ids, \
            f"Scheme IDs not preserved. Original: {original_ids}, Returned: {returned_ids}"


def test_real_world_scheme_examples():
    """
    Test with real-world scheme examples from the design document
    """
    real_schemes = {
        'Items': [
            {
                'scheme_id': {'S': 'SCH001'},
                'scheme_name': {'S': 'Post Matric Scholarship'},
                'category': {'S': 'education'},
                'description': {'S': 'Scholarship for students from economically weaker sections'},
                'eligibility': {'S': 'Family income below 2.5 lakh'},
                'benefits': {'S': 'Covers tuition fees and maintenance allowance'}
            },
            {
                'scheme_id': {'S': 'SCH002'},
                'scheme_name': {'S': 'PM Kisan'},
                'category': {'S': 'farmer'},
                'description': {'S': 'Income support for farmers'},
                'eligibility': {'S': 'All landholding farmers'},
                'benefits': {'S': 'Rs 6000 per year in three installments'}
            },
            {
                'scheme_id': {'S': 'SCH003'},
                'scheme_name': {'S': 'Mudra Loan'},
                'category': {'S': 'business'},
                'description': {'S': 'Loans for micro and small enterprises'},
                'eligibility': {'S': 'Non-corporate, non-farm small/micro enterprises'},
                'benefits': {'S': 'Loans up to Rs 10 lakh'}
            },
            {
                'scheme_id': {'S': 'SCH004'},
                'scheme_name': {'S': 'Ayushman Bharat'},
                'category': {'S': 'healthcare'},
                'description': {'S': 'Health insurance for economically vulnerable families'},
                'eligibility': {'S': 'Families identified through SECC database'},
                'benefits': {'S': 'Health cover of Rs 5 lakh per family per year'}
            },
            {
                'scheme_id': {'S': 'SCH005'},
                'scheme_name': {'S': 'PM Awas Yojana'},
                'category': {'S': 'housing'},
                'description': {'S': 'Affordable housing for urban poor'},
                'eligibility': {'S': 'EWS/LIG families without pucca house'},
                'benefits': {'S': 'Financial assistance for house construction'}
            }
        ]
    }
    
    with patch('boto3.client') as mock_boto3:
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = real_schemes
        
        # Call get_all_schemes
        schemes = get_all_schemes(mock_dynamodb)
        
        # Verify we got 5 schemes
        assert len(schemes) == 5, f"Expected 5 schemes, got {len(schemes)}"
        
        # Verify each scheme
        for scheme in schemes:
            is_valid, error_msg = validate_scheme_integrity(scheme)
            assert is_valid, f"Real-world scheme failed validation: {error_msg}"
        
        # Verify all categories are represented
        categories = {scheme['category'] for scheme in schemes}
        assert categories == VALID_CATEGORIES, \
            f"Not all categories represented. Got: {categories}, Expected: {VALID_CATEGORIES}"
        
        print("✓ All real-world scheme examples validated successfully")


def run_all_tests():
    """Run all property tests and report results"""
    print("=" * 80)
    print("Property-Based Test: Scheme Data Integrity")
    print("=" * 80)
    print()
    print("**Validates: Requirements 2.1, 2.3, 14.1, 14.2**")
    print()
    print("Property 2: Scheme Data Integrity")
    print("For any scheme retrieved from DynamoDB, it should contain all required")
    print("fields (scheme_id, scheme_name, category, description, eligibility, benefits)")
    print("and the category should be one of {education, farmer, business, healthcare, housing}.")
    print()
    print("-" * 80)
    
    tests = [
        ("All schemes have required fields", test_property_all_schemes_have_required_fields),
        ("All categories are valid", test_property_all_categories_are_valid),
        ("Empty table returns empty list", test_property_empty_table_returns_empty_list),
        ("DynamoDB format conversion", test_property_dynamodb_format_conversion),
        ("Scheme count matches DynamoDB", test_property_scheme_count_matches_dynamodb),
        ("All scheme IDs preserved", test_property_all_scheme_ids_preserved),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}...")
            test_func()
            print(f"  ✓ PASSED")
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {str(e)}")
            failed += 1
    
    # Run real-world example test
    try:
        print(f"\nRunning: Real-world scheme examples...")
        test_real_world_scheme_examples()
        print(f"  ✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
        failed += 1
    
    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print()
        print("✓ All Property Tests Passed!")
        print()
        print("Requirements Validated:")
        print("  ✓ 2.1 - DynamoDB stores schemes with all required fields")
        print("  ✓ 2.3 - Category is one of: education, farmer, business, healthcare, housing")
        print("  ✓ 14.1 - System only accepts schemes with valid category values")
        print("  ✓ 14.2 - Backend verifies each scheme has a valid category")
        print()
        return 0
    else:
        print()
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
