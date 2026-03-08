#!/usr/bin/env python3
"""
Property-Based Test: Context Building Completeness

**Validates: Requirements 2.5, 10.4, 10.5**

Property 4: Context Building Completeness
For any list of schemes, when building context, all scheme names should appear in 
the resulting context string, or if the list is empty, the context should indicate 
"No schemes available in database."

This test verifies that the context building process includes all schemes and
their complete information without loss or corruption.
"""

import json
import sys
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, Any, List

# Import the lambda function
sys.path.insert(0, '.')
from lambda_function import build_context

# Valid categories as per requirements
VALID_CATEGORIES = ['education', 'farmer', 'business', 'healthcare', 'housing']

# Required fields for a scheme
REQUIRED_FIELDS = ['scheme_id', 'scheme_name', 'category', 'description', 'eligibility', 'benefits']


# Strategy for generating valid scheme dictionaries (already converted from DynamoDB format)
@st.composite
def scheme_dict(draw):
    """Generate a valid scheme dictionary in Python format"""
    scheme_id = draw(st.text(
        alphabet=st.characters(min_codepoint=65, max_codepoint=90, blacklist_categories=()),
        min_size=3,
        max_size=15
    ))
    scheme_name = draw(st.text(min_size=5, max_size=200))
    category = draw(st.sampled_from(VALID_CATEGORIES))
    description = draw(st.text(min_size=10, max_size=500))
    eligibility = draw(st.text(min_size=5, max_size=300))
    benefits = draw(st.text(min_size=5, max_size=300))
    
    return {
        'scheme_id': scheme_id,
        'scheme_name': scheme_name,
        'category': category,
        'description': description,
        'eligibility': eligibility,
        'benefits': benefits
    }


@st.composite
def schemes_list(draw, min_size=0, max_size=20):
    """Generate a list of unique scheme dictionaries"""
    num_schemes = draw(st.integers(min_value=min_size, max_value=max_size))
    schemes = []
    seen_ids = set()
    
    for _ in range(num_schemes):
        scheme = draw(scheme_dict())
        # Ensure unique scheme_id
        while scheme['scheme_id'] in seen_ids:
            scheme = draw(scheme_dict())
        seen_ids.add(scheme['scheme_id'])
        schemes.append(scheme)
    
    return schemes


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_all_scheme_names_in_context(schemes):
    """
    Property Test: All scheme names appear in context
    
    For any list of schemes, the build_context function should include
    all scheme names in the resulting context string.
    """
    # Build context
    context = build_context(schemes)
    
    # Verify context is a string
    assert isinstance(context, str), "Context should be a string"
    
    # Verify all scheme names are present
    for scheme in schemes:
        scheme_name = scheme['scheme_name']
        assert scheme_name in context, \
            f"Scheme name '{scheme_name}' not found in context. " \
            f"Context building is incomplete."


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_all_scheme_fields_in_context(schemes):
    """
    Property Test: All scheme fields appear in context
    
    For any list of schemes, the build_context function should include
    all fields (name, category, description, eligibility, benefits) for
    each scheme in the resulting context string.
    """
    # Build context
    context = build_context(schemes)
    
    # Verify all fields for each scheme are present
    for scheme in schemes:
        for field in ['scheme_name', 'category', 'description', 'eligibility', 'benefits']:
            field_value = scheme[field]
            assert field_value in context, \
                f"Field '{field}' with value '{field_value}' not found in context " \
                f"for scheme '{scheme['scheme_name']}'. Context building is incomplete."


@given(schemes_list(min_size=0, max_size=0))
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_empty_schemes_message(empty_schemes):
    """
    Property Test: Empty schemes list returns appropriate message
    
    When the schemes list is empty, build_context should return
    "No schemes available in database."
    """
    # Build context
    context = build_context(empty_schemes)
    
    # Verify the expected message
    assert context == "No schemes available in database.", \
        f"Expected 'No schemes available in database.' for empty list, " \
        f"but got: '{context}'"


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_context_is_non_empty_string(schemes):
    """
    Property Test: Context is always a non-empty string
    
    For any non-empty list of schemes, build_context should return
    a non-empty string.
    """
    # Build context
    context = build_context(schemes)
    
    # Verify context is non-empty string
    assert isinstance(context, str), "Context should be a string"
    assert len(context) > 0, "Context should not be empty for non-empty schemes list"


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_context_is_valid_utf8(schemes):
    """
    Property Test: Context is valid UTF-8 string
    
    For any list of schemes, the build_context function should return
    a valid UTF-8 encoded string (as per Requirement 10.5).
    """
    # Build context
    context = build_context(schemes)
    
    # Verify UTF-8 encoding
    try:
        encoded = context.encode('utf-8')
        decoded = encoded.decode('utf-8')
        assert decoded == context, "Context should be valid UTF-8"
    except UnicodeEncodeError:
        assert False, "Context contains invalid UTF-8 characters"
    except UnicodeDecodeError:
        assert False, "Context cannot be decoded as UTF-8"


@given(schemes_list(min_size=2, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.large_base_example])
def test_property_schemes_separated_by_delimiter(schemes):
    """
    Property Test: Schemes are separated by clear delimiters
    
    For any list with multiple schemes, the context should contain
    delimiters separating each scheme (as per Requirement 10.2).
    """
    # Build context
    context = build_context(schemes)
    
    # Count delimiter occurrences (using "---" as delimiter)
    delimiter_count = context.count('---')
    
    # Should have one delimiter per scheme
    assert delimiter_count == len(schemes), \
        f"Expected {len(schemes)} delimiters ('---'), but found {delimiter_count}. " \
        f"Schemes are not properly separated."


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_no_scheme_data_loss(schemes):
    """
    Property Test: No data loss during context building
    
    For any list of schemes, all data from all schemes should be
    present in the context. No information should be lost.
    """
    # Build context
    context = build_context(schemes)
    
    # Verify each scheme's complete data is in context
    for i, scheme in enumerate(schemes):
        # Check all field values are present
        for field, value in scheme.items():
            if field != 'scheme_id':  # scheme_id is not included in context format
                assert value in context, \
                    f"Data loss detected: Field '{field}' value '{value}' " \
                    f"from scheme {i} not found in context."


@given(st.integers(min_value=1, max_value=50))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_context_completeness_by_count(num_schemes):
    """
    Property Test: Context completeness for any number of schemes
    
    For any number N of schemes (1 to 50), the context should contain
    all N scheme names. This tests completeness across different list sizes.
    """
    # Generate N schemes
    schemes = []
    for i in range(num_schemes):
        schemes.append({
            'scheme_id': f'SCH{i:03d}',
            'scheme_name': f'Scheme {i}',
            'category': VALID_CATEGORIES[i % len(VALID_CATEGORIES)],
            'description': f'Description for scheme {i}',
            'eligibility': f'Eligibility for scheme {i}',
            'benefits': f'Benefits for scheme {i}'
        })
    
    # Build context
    context = build_context(schemes)
    
    # Verify all scheme names are present
    for scheme in schemes:
        assert scheme['scheme_name'] in context, \
            f"Scheme name '{scheme['scheme_name']}' not found in context. " \
            f"Context is incomplete for {num_schemes} schemes."


@given(schemes_list(min_size=1, max_size=10))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_context_format_consistency(schemes):
    """
    Property Test: Context format is consistent
    
    For any list of schemes, the context should follow a consistent
    format with labeled fields (Scheme:, Category:, Description:, etc.)
    """
    # Build context
    context = build_context(schemes)
    
    # Verify format labels are present for each scheme
    expected_labels = ['Scheme:', 'Category:', 'Description:', 'Eligibility:', 'Benefits:']
    
    for label in expected_labels:
        label_count = context.count(label)
        assert label_count == len(schemes), \
            f"Expected {len(schemes)} occurrences of '{label}', but found {label_count}. " \
            f"Context format is inconsistent."


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_all_categories_in_context(schemes):
    """
    Property Test: All scheme categories appear in context
    
    For any list of schemes, all category values should be present
    in the context string (as per Requirement 14.3).
    """
    # Build context
    context = build_context(schemes)
    
    # Verify all categories are present
    for scheme in schemes:
        category = scheme['category']
        assert category in context, \
            f"Category '{category}' not found in context for scheme '{scheme['scheme_name']}'. " \
            f"Context building is incomplete."


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_no_duplicate_scheme_names(schemes):
    """
    Property Test: Each scheme appears exactly once in context
    
    For any list of schemes with unique IDs, each scheme name should
    appear exactly once in the context (no duplicates, no omissions).
    
    Note: This test checks that each scheme name appears at least once.
    If a scheme name is a substring of another field value, it may appear
    multiple times, which is acceptable as long as it appears at least once.
    """
    # Build context
    context = build_context(schemes)
    
    # Verify each scheme name appears at least once
    for scheme in schemes:
        scheme_name = scheme['scheme_name']
        count = context.count(scheme_name)
        assert count >= 1, \
            f"Scheme name '{scheme_name}' appears {count} times in context, " \
            f"expected at least 1. Context building has omission issues."


def test_real_world_context_completeness():
    """
    Test context completeness with real-world scheme examples
    
    Verify that all 5 real-world schemes from the design document are
    included completely in the context.
    """
    real_schemes = [
        {
            'scheme_id': 'SCH001',
            'scheme_name': 'Post Matric Scholarship',
            'category': 'education',
            'description': 'Scholarship for students from economically weaker sections',
            'eligibility': 'Family income below 2.5 lakh',
            'benefits': 'Covers tuition fees and maintenance allowance'
        },
        {
            'scheme_id': 'SCH002',
            'scheme_name': 'PM Kisan',
            'category': 'farmer',
            'description': 'Income support for farmers',
            'eligibility': 'All landholding farmers',
            'benefits': 'Rs 6000 per year in three installments'
        },
        {
            'scheme_id': 'SCH003',
            'scheme_name': 'Mudra Loan',
            'category': 'business',
            'description': 'Loans for micro and small enterprises',
            'eligibility': 'Non-corporate, non-farm small/micro enterprises',
            'benefits': 'Loans up to Rs 10 lakh'
        },
        {
            'scheme_id': 'SCH004',
            'scheme_name': 'Ayushman Bharat',
            'category': 'healthcare',
            'description': 'Health insurance for economically vulnerable families',
            'eligibility': 'Families identified through SECC database',
            'benefits': 'Health cover of Rs 5 lakh per family per year'
        },
        {
            'scheme_id': 'SCH005',
            'scheme_name': 'PM Awas Yojana',
            'category': 'housing',
            'description': 'Affordable housing for urban poor',
            'eligibility': 'EWS/LIG families without pucca house',
            'benefits': 'Financial assistance for house construction'
        }
    ]
    
    # Build context
    context = build_context(real_schemes)
    
    # Verify all scheme names are present
    expected_names = [
        'Post Matric Scholarship',
        'PM Kisan',
        'Mudra Loan',
        'Ayushman Bharat',
        'PM Awas Yojana'
    ]
    
    for name in expected_names:
        assert name in context, \
            f"Real-world scheme '{name}' not found in context. Context is incomplete."
    
    # Verify all categories are present
    expected_categories = ['education', 'farmer', 'business', 'healthcare', 'housing']
    for category in expected_categories:
        assert category in context, \
            f"Category '{category}' not found in context. Context is incomplete."
    
    # Verify all descriptions are present
    for scheme in real_schemes:
        assert scheme['description'] in context, \
            f"Description for '{scheme['scheme_name']}' not found in context."
        assert scheme['eligibility'] in context, \
            f"Eligibility for '{scheme['scheme_name']}' not found in context."
        assert scheme['benefits'] in context, \
            f"Benefits for '{scheme['scheme_name']}' not found in context."
    
    # Verify proper formatting
    assert context.count('---') == 5, "Expected 5 scheme delimiters"
    assert context.count('Scheme:') == 5, "Expected 5 'Scheme:' labels"
    assert context.count('Category:') == 5, "Expected 5 'Category:' labels"
    
    print("✓ All 5 real-world schemes included completely in context")


def test_empty_schemes_list():
    """
    Test that empty schemes list returns the expected message
    """
    empty_schemes = []
    context = build_context(empty_schemes)
    
    assert context == "No schemes available in database.", \
        f"Expected 'No schemes available in database.' for empty list, got: '{context}'"
    
    print("✓ Empty schemes list returns correct message")


def test_single_scheme_context():
    """
    Test context building with a single scheme
    """
    single_scheme = [{
        'scheme_id': 'SCH001',
        'scheme_name': 'Test Scheme',
        'category': 'education',
        'description': 'Test description',
        'eligibility': 'Test eligibility',
        'benefits': 'Test benefits'
    }]
    
    context = build_context(single_scheme)
    
    # Verify all fields are present
    assert 'Test Scheme' in context
    assert 'education' in context
    assert 'Test description' in context
    assert 'Test eligibility' in context
    assert 'Test benefits' in context
    
    # Verify format
    assert 'Scheme:' in context
    assert 'Category:' in context
    assert 'Description:' in context
    assert 'Eligibility:' in context
    assert 'Benefits:' in context
    assert '---' in context
    
    print("✓ Single scheme context built correctly")


def run_all_tests():
    """Run all property tests and report results"""
    print("=" * 80)
    print("Property-Based Test: Context Building Completeness")
    print("=" * 80)
    print()
    print("**Validates: Requirements 2.5, 10.4, 10.5**")
    print()
    print("Property 4: Context Building Completeness")
    print("For any list of schemes, when building context, all scheme names should")
    print("appear in the resulting context string, or if the list is empty, the")
    print("context should indicate 'No schemes available in database.'")
    print()
    print("-" * 80)
    
    tests = [
        ("All scheme names in context", test_property_all_scheme_names_in_context),
        ("All scheme fields in context", test_property_all_scheme_fields_in_context),
        ("Empty schemes message", test_property_empty_schemes_message),
        ("Context is non-empty string", test_property_context_is_non_empty_string),
        ("Context is valid UTF-8", test_property_context_is_valid_utf8),
        ("Schemes separated by delimiter", test_property_schemes_separated_by_delimiter),
        ("No scheme data loss", test_property_no_scheme_data_loss),
        ("Context completeness by count", test_property_context_completeness_by_count),
        ("Context format consistency", test_property_context_format_consistency),
        ("All categories in context", test_property_all_categories_in_context),
        ("No duplicate scheme names", test_property_no_duplicate_scheme_names),
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
    
    # Run example tests
    example_tests = [
        ("Real-world context completeness", test_real_world_context_completeness),
        ("Empty schemes list", test_empty_schemes_list),
        ("Single scheme context", test_single_scheme_context),
    ]
    
    for test_name, test_func in example_tests:
        try:
            print(f"\nRunning: {test_name}...")
            test_func()
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
        print("  ✓ 2.5 - Backend includes all retrieved schemes in formatted context")
        print("  ✓ 10.4 - All scheme names appear in context string")
        print("  ✓ 10.5 - Context is valid UTF-8 string")
        print()
        print("Completeness Guarantees:")
        print("  ✓ All scheme names are included in context")
        print("  ✓ All scheme fields (name, category, description, eligibility, benefits)")
        print("    are included for each scheme")
        print("  ✓ Empty schemes list returns appropriate message")
        print("  ✓ Context is properly formatted with delimiters")
        print("  ✓ No data loss during context building")
        print("  ✓ Context is valid UTF-8 encoded")
        print()
        return 0
    else:
        print()
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
