#!/usr/bin/env python3
"""
Property-Based Test: Scheme Context Formatting

**Validates: Requirements 10.1, 14.3**

Property 12: Scheme Context Formatting
For any scheme included in the context, all its fields (name, category, description, 
eligibility, benefits) should appear in the formatted context string.

This test verifies that the context building process properly formats each scheme
with all required fields visible in the output string.
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

# Required fields that should appear in context
CONTEXT_FIELDS = ['scheme_name', 'category', 'description', 'eligibility', 'benefits']


# Strategy for generating valid scheme dictionaries
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


@given(scheme_dict())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_single_scheme_all_fields_in_context(scheme):
    """
    Property Test: All fields of a single scheme appear in context
    
    For any scheme, when building context, all fields (name, category, 
    description, eligibility, benefits) should appear in the formatted string.
    """
    # Build context with single scheme
    context = build_context([scheme])
    
    # Verify context is a string
    assert isinstance(context, str), "Context should be a string"
    
    # Verify all required fields are present in context
    for field in CONTEXT_FIELDS:
        field_value = scheme[field]
        assert field_value in context, \
            f"Field '{field}' with value '{field_value}' not found in context. " \
            f"Context formatting is incomplete."


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_all_scheme_fields_formatted_in_context(schemes):
    """
    Property Test: All fields for all schemes appear in context
    
    For any list of schemes, the build_context function should include
    all fields (name, category, description, eligibility, benefits) for
    each scheme in the resulting context string.
    """
    # Build context
    context = build_context(schemes)
    
    # Verify all fields for each scheme are present
    for i, scheme in enumerate(schemes):
        for field in CONTEXT_FIELDS:
            field_value = scheme[field]
            assert field_value in context, \
                f"Scheme {i}: Field '{field}' with value '{field_value}' not found in context. " \
                f"Context formatting is incomplete."


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_category_field_in_context(schemes):
    """
    Property Test: Category field appears in context for each scheme
    
    For any scheme included in the context, the category field should
    appear in the formatted context string (Requirement 14.3).
    """
    # Build context
    context = build_context(schemes)
    
    # Verify category for each scheme is present
    for i, scheme in enumerate(schemes):
        category = scheme['category']
        assert category in context, \
            f"Scheme {i}: Category '{category}' not found in context. " \
            f"Requirement 14.3 violated: category field must be included."


@given(schemes_list(min_size=1, max_size=10))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_context_has_field_labels(schemes):
    """
    Property Test: Context includes field labels for formatting
    
    For any list of schemes, the context should include field labels
    (Scheme:, Category:, Description:, Eligibility:, Benefits:) to
    clearly identify each field (Requirement 10.1).
    """
    # Build context
    context = build_context(schemes)
    
    # Expected labels in the format
    expected_labels = ['Scheme:', 'Category:', 'Description:', 'Eligibility:', 'Benefits:']
    
    # Verify each label appears the correct number of times
    for label in expected_labels:
        label_count = context.count(label)
        assert label_count == len(schemes), \
            f"Expected {len(schemes)} occurrences of '{label}', but found {label_count}. " \
            f"Context formatting is inconsistent (Requirement 10.1)."


@given(scheme_dict())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_scheme_name_formatted_correctly(scheme):
    """
    Property Test: Scheme name is formatted with label
    
    For any scheme, the scheme_name should appear in the context
    with the "Scheme:" label prefix.
    """
    # Build context
    context = build_context([scheme])
    
    # Verify scheme name appears with label
    scheme_name = scheme['scheme_name']
    assert f"Scheme: {scheme_name}" in context, \
        f"Scheme name '{scheme_name}' not formatted correctly with 'Scheme:' label. " \
        f"Context formatting requirement violated."


@given(scheme_dict())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_category_formatted_correctly(scheme):
    """
    Property Test: Category is formatted with label
    
    For any scheme, the category should appear in the context
    with the "Category:" label prefix.
    """
    # Build context
    context = build_context([scheme])
    
    # Verify category appears with label
    category = scheme['category']
    assert f"Category: {category}" in context, \
        f"Category '{category}' not formatted correctly with 'Category:' label. " \
        f"Context formatting requirement violated."


@given(scheme_dict())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_description_formatted_correctly(scheme):
    """
    Property Test: Description is formatted with label
    
    For any scheme, the description should appear in the context
    with the "Description:" label prefix.
    """
    # Build context
    context = build_context([scheme])
    
    # Verify description appears with label
    description = scheme['description']
    assert f"Description: {description}" in context, \
        f"Description not formatted correctly with 'Description:' label. " \
        f"Context formatting requirement violated."


@given(scheme_dict())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_eligibility_formatted_correctly(scheme):
    """
    Property Test: Eligibility is formatted with label
    
    For any scheme, the eligibility should appear in the context
    with the "Eligibility:" label prefix.
    """
    # Build context
    context = build_context([scheme])
    
    # Verify eligibility appears with label
    eligibility = scheme['eligibility']
    assert f"Eligibility: {eligibility}" in context, \
        f"Eligibility not formatted correctly with 'Eligibility:' label. " \
        f"Context formatting requirement violated."


@given(scheme_dict())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_benefits_formatted_correctly(scheme):
    """
    Property Test: Benefits is formatted with label
    
    For any scheme, the benefits should appear in the context
    with the "Benefits:" label prefix.
    """
    # Build context
    context = build_context([scheme])
    
    # Verify benefits appears with label
    benefits = scheme['benefits']
    assert f"Benefits: {benefits}" in context, \
        f"Benefits not formatted correctly with 'Benefits:' label. " \
        f"Context formatting requirement violated."


@given(schemes_list(min_size=1, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_all_categories_visible_in_context(schemes):
    """
    Property Test: All scheme categories are visible in context
    
    For any list of schemes, all category values should be visible
    in the formatted context string (Requirement 14.3).
    """
    # Build context
    context = build_context(schemes)
    
    # Verify all categories are visible
    for i, scheme in enumerate(schemes):
        category = scheme['category']
        assert category in context, \
            f"Scheme {i}: Category '{category}' not visible in context. " \
            f"Requirement 14.3 violated."


@given(schemes_list(min_size=2, max_size=10))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.large_base_example])
def test_property_field_order_consistency(schemes):
    """
    Property Test: Fields appear in consistent order for all schemes
    
    For any list of schemes, the fields should appear in the same order
    for each scheme (Scheme, Category, Description, Eligibility, Benefits).
    """
    # Build context
    context = build_context(schemes)
    
    # Split context by delimiter to get individual scheme sections
    scheme_sections = context.split('---')
    
    # Remove empty sections
    scheme_sections = [s.strip() for s in scheme_sections if s.strip()]
    
    # Verify we have the right number of sections
    assert len(scheme_sections) == len(schemes), \
        f"Expected {len(schemes)} scheme sections, got {len(scheme_sections)}"
    
    # Verify field order in each section
    expected_order = ['Scheme:', 'Category:', 'Description:', 'Eligibility:', 'Benefits:']
    
    for i, section in enumerate(scheme_sections):
        # Find positions of each label
        positions = {}
        for label in expected_order:
            pos = section.find(label)
            assert pos != -1, f"Section {i}: Label '{label}' not found"
            positions[label] = pos
        
        # Verify order
        prev_pos = -1
        for label in expected_order:
            curr_pos = positions[label]
            assert curr_pos > prev_pos, \
                f"Section {i}: Field order incorrect. '{label}' appears before expected position."
            prev_pos = curr_pos


@given(scheme_dict())
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_no_field_value_truncation(scheme):
    """
    Property Test: Field values are not truncated in context
    
    For any scheme, all field values should appear in their entirety
    in the context (no truncation or abbreviation).
    """
    # Build context
    context = build_context([scheme])
    
    # Verify complete field values are present
    for field in CONTEXT_FIELDS:
        field_value = scheme[field]
        # Check that the complete value is in context
        assert field_value in context, \
            f"Field '{field}' value appears to be truncated or missing. " \
            f"Expected complete value: '{field_value}'"
        
        # Verify the value length matches (no truncation)
        value_occurrences = context.count(field_value)
        assert value_occurrences >= 1, \
            f"Field '{field}' value not found in context"


def test_real_world_scheme_formatting():
    """
    Test context formatting with real-world scheme examples
    
    Verify that all fields of real-world schemes are properly formatted
    in the context with correct labels and structure.
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
        }
    ]
    
    # Build context
    context = build_context(real_schemes)
    
    # Verify all fields for each scheme are present
    for scheme in real_schemes:
        # Check scheme name with label
        assert f"Scheme: {scheme['scheme_name']}" in context, \
            f"Scheme name '{scheme['scheme_name']}' not properly formatted"
        
        # Check category with label
        assert f"Category: {scheme['category']}" in context, \
            f"Category '{scheme['category']}' not properly formatted"
        
        # Check description with label
        assert f"Description: {scheme['description']}" in context, \
            f"Description not properly formatted for '{scheme['scheme_name']}'"
        
        # Check eligibility with label
        assert f"Eligibility: {scheme['eligibility']}" in context, \
            f"Eligibility not properly formatted for '{scheme['scheme_name']}'"
        
        # Check benefits with label
        assert f"Benefits: {scheme['benefits']}" in context, \
            f"Benefits not properly formatted for '{scheme['scheme_name']}'"
    
    # Verify field labels appear correct number of times
    assert context.count('Scheme:') == 3, "Expected 3 'Scheme:' labels"
    assert context.count('Category:') == 3, "Expected 3 'Category:' labels"
    assert context.count('Description:') == 3, "Expected 3 'Description:' labels"
    assert context.count('Eligibility:') == 3, "Expected 3 'Eligibility:' labels"
    assert context.count('Benefits:') == 3, "Expected 3 'Benefits:' labels"
    
    # Verify delimiters
    assert context.count('---') == 3, "Expected 3 scheme delimiters"
    
    print("✓ All real-world schemes properly formatted with all fields")


def test_single_scheme_complete_formatting():
    """
    Test that a single scheme has all fields properly formatted
    """
    single_scheme = {
        'scheme_id': 'TEST001',
        'scheme_name': 'Test Scheme Name',
        'category': 'education',
        'description': 'This is a test description',
        'eligibility': 'Test eligibility criteria',
        'benefits': 'Test benefits information'
    }
    
    # Build context
    context = build_context([single_scheme])
    
    # Verify all fields with labels
    assert 'Scheme: Test Scheme Name' in context
    assert 'Category: education' in context
    assert 'Description: This is a test description' in context
    assert 'Eligibility: Test eligibility criteria' in context
    assert 'Benefits: Test benefits information' in context
    
    # Verify delimiter
    assert '---' in context
    
    print("✓ Single scheme formatted correctly with all fields and labels")


def test_multiple_categories_formatting():
    """
    Test that schemes from all categories are properly formatted
    """
    schemes_all_categories = [
        {
            'scheme_id': 'EDU001',
            'scheme_name': 'Education Scheme',
            'category': 'education',
            'description': 'Education description',
            'eligibility': 'Education eligibility',
            'benefits': 'Education benefits'
        },
        {
            'scheme_id': 'FAR001',
            'scheme_name': 'Farmer Scheme',
            'category': 'farmer',
            'description': 'Farmer description',
            'eligibility': 'Farmer eligibility',
            'benefits': 'Farmer benefits'
        },
        {
            'scheme_id': 'BUS001',
            'scheme_name': 'Business Scheme',
            'category': 'business',
            'description': 'Business description',
            'eligibility': 'Business eligibility',
            'benefits': 'Business benefits'
        },
        {
            'scheme_id': 'HEA001',
            'scheme_name': 'Healthcare Scheme',
            'category': 'healthcare',
            'description': 'Healthcare description',
            'eligibility': 'Healthcare eligibility',
            'benefits': 'Healthcare benefits'
        },
        {
            'scheme_id': 'HOU001',
            'scheme_name': 'Housing Scheme',
            'category': 'housing',
            'description': 'Housing description',
            'eligibility': 'Housing eligibility',
            'benefits': 'Housing benefits'
        }
    ]
    
    # Build context
    context = build_context(schemes_all_categories)
    
    # Verify all categories are formatted
    for scheme in schemes_all_categories:
        assert f"Category: {scheme['category']}" in context, \
            f"Category '{scheme['category']}' not properly formatted"
    
    # Verify all categories appear
    assert 'education' in context
    assert 'farmer' in context
    assert 'business' in context
    assert 'healthcare' in context
    assert 'housing' in context
    
    print("✓ All 5 categories properly formatted in context")


def run_all_tests():
    """Run all property tests and report results"""
    print("=" * 80)
    print("Property-Based Test: Scheme Context Formatting")
    print("=" * 80)
    print()
    print("**Validates: Requirements 10.1, 14.3**")
    print()
    print("Property 12: Scheme Context Formatting")
    print("For any scheme included in the context, all its fields (name, category,")
    print("description, eligibility, benefits) should appear in the formatted context string.")
    print()
    print("-" * 80)
    
    tests = [
        ("Single scheme all fields in context", test_property_single_scheme_all_fields_in_context),
        ("All scheme fields formatted in context", test_property_all_scheme_fields_formatted_in_context),
        ("Category field in context", test_property_category_field_in_context),
        ("Context has field labels", test_property_context_has_field_labels),
        ("Scheme name formatted correctly", test_property_scheme_name_formatted_correctly),
        ("Category formatted correctly", test_property_category_formatted_correctly),
        ("Description formatted correctly", test_property_description_formatted_correctly),
        ("Eligibility formatted correctly", test_property_eligibility_formatted_correctly),
        ("Benefits formatted correctly", test_property_benefits_formatted_correctly),
        ("All categories visible in context", test_property_all_categories_visible_in_context),
        ("Field order consistency", test_property_field_order_consistency),
        ("No field value truncation", test_property_no_field_value_truncation),
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
        ("Real-world scheme formatting", test_real_world_scheme_formatting),
        ("Single scheme complete formatting", test_single_scheme_complete_formatting),
        ("Multiple categories formatting", test_multiple_categories_formatting),
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
        print("  ✓ 10.1 - Each scheme formatted with name, category, description,")
        print("           eligibility, and benefits with clear labels")
        print("  ✓ 14.3 - Category field included in context for each scheme")
        print()
        print("Formatting Guarantees:")
        print("  ✓ All scheme fields appear in context with proper labels")
        print("  ✓ Field labels (Scheme:, Category:, etc.) are consistent")
        print("  ✓ Field order is consistent across all schemes")
        print("  ✓ No field values are truncated or abbreviated")
        print("  ✓ All categories are visible in formatted context")
        print("  ✓ Each scheme section is properly delimited")
        print()
        return 0
    else:
        print()
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
