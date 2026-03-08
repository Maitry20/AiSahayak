#!/usr/bin/env python3
"""
Property-Based Test: Query Length Limit

**Validates: Requirements 1.3**

Property 9: Query Length Limit
For any query exceeding 1000 characters, the System should reject it.

This test verifies that query length validation works correctly, including:
- Queries with length > 1000 characters are rejected with 400
- Queries with length <= 1000 characters are accepted (or processed normally)
- CORS headers are present in all responses
- Error messages are appropriate for length violations
"""

import json
import sys
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings, HealthCheck

# Import the lambda function
sys.path.insert(0, '.')
from lambda_function import lambda_handler


# Strategy for generating queries at the boundary (exactly 1000 characters)
boundary_query_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=1000,
    max_size=1000
).filter(lambda x: x.strip() != '')

# Strategy for generating queries just under the limit (< 1000 characters)
under_limit_query_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=1,
    max_size=999
).filter(lambda x: x.strip() != '')

# Strategy for generating queries over the limit (> 1000 characters)
over_limit_query_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=1001,
    max_size=2000
)

# Strategy for generating queries significantly over the limit
far_over_limit_query_strategy = st.text(
    min_size=1001,
    max_size=5000
)


# Strategy for generating API Gateway events
@st.composite
def api_gateway_event_with_query(draw, query_strategy):
    """Generate API Gateway event with specified query"""
    query = draw(query_strategy)
    body = json.dumps({'query': query})
    return {
        'body': body,
        'headers': {'Content-Type': 'application/json'},
        'httpMethod': 'POST',
        'path': '/query'
    }


def mock_dynamodb_response():
    """Create a mock DynamoDB response"""
    return {
        'Items': [
            {
                'scheme_id': {'S': 'SCH001'},
                'scheme_name': {'S': 'Post Matric Scholarship'},
                'category': {'S': 'education'},
                'description': {'S': 'Scholarship for students'},
                'eligibility': {'S': 'Family income below 2.5 lakh'},
                'benefits': {'S': 'Covers tuition fees'}
            }
        ]
    }


def mock_bedrock_response():
    """Create a mock Bedrock response"""
    response_body = {
        'output': {
            'message': {
                'content': [
                    {'text': 'Based on your query, here are relevant schemes.'}
                ]
            }
        }
    }
    
    mock_body = Mock()
    mock_body.read.return_value = json.dumps(response_body).encode('utf-8')
    
    return {
        'body': mock_body,
        'ResponseMetadata': {'HTTPStatusCode': 200}
    }


@given(api_gateway_event_with_query(over_limit_query_strategy))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_query_over_1000_chars_rejected_with_400(event):
    """
    Property Test: Queries exceeding 1000 characters are rejected with 400
    
    For any query with length > 1000 characters, the Backend should:
    - Return statusCode 400
    - Include CORS headers
    - Return error message in body mentioning length limit
    """
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify 400 status code
        assert response['statusCode'] == 400, \
            f"Expected statusCode 400 for query > 1000 chars, got {response['statusCode']}"
        
        # Verify CORS headers present
        assert 'Access-Control-Allow-Origin' in response['headers'], \
            "CORS headers must be present in error response"
        
        # Verify error message in body
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain 'error' field"
        
        # Check that error message mentions length or maximum
        error_msg = body['error'].lower()
        assert 'length' in error_msg or 'maximum' in error_msg or 'exceeds' in error_msg or '1000' in error_msg, \
            f"Error message should mention length limit, got: {body['error']}"


@given(api_gateway_event_with_query(under_limit_query_strategy))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_query_under_1000_chars_accepted(event):
    """
    Property Test: Queries with length <= 1000 characters are accepted
    
    For any query with length < 1000 characters (and non-empty), the Backend should:
    - NOT return statusCode 400 for length reasons
    - Process the query normally
    - Return statusCode 200 (success) or 500 (service error), but not 400
    """
    with patch('boto3.client') as mock_boto3:
        # Mock DynamoDB client
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_dynamodb_response()
        
        # Mock Bedrock client
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = mock_bedrock_response()
        
        # Configure boto3.client to return appropriate mocks
        def client_side_effect(service, **kwargs):
            if service == 'dynamodb':
                return mock_dynamodb
            elif service == 'bedrock-runtime':
                return mock_bedrock
            return Mock()
        
        mock_boto3.side_effect = client_side_effect
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify NOT 400 (should be accepted)
        # Note: Could be 200 (success) or 500 (service error), but not 400 (validation error)
        assert response['statusCode'] in [200, 500], \
            f"Query under 1000 chars should not be rejected with 400, got {response['statusCode']}"
        
        # Verify CORS headers present
        assert 'Access-Control-Allow-Origin' in response['headers'], \
            "CORS headers must be present in response"


@given(api_gateway_event_with_query(boundary_query_strategy))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_query_exactly_1000_chars_accepted(event):
    """
    Property Test: Queries with exactly 1000 characters are accepted
    
    For any query with length exactly 1000 characters, the Backend should:
    - Accept the query (1000 is the limit, not over the limit)
    - Process the query normally
    - Return statusCode 200 (success) or 500 (service error), but not 400
    """
    with patch('boto3.client') as mock_boto3:
        # Mock DynamoDB client
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_dynamodb_response()
        
        # Mock Bedrock client
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = mock_bedrock_response()
        
        # Configure boto3.client to return appropriate mocks
        def client_side_effect(service, **kwargs):
            if service == 'dynamodb':
                return mock_dynamodb
            elif service == 'bedrock-runtime':
                return mock_bedrock
            return Mock()
        
        mock_boto3.side_effect = client_side_effect
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify NOT 400 (exactly 1000 should be accepted)
        assert response['statusCode'] in [200, 500], \
            f"Query with exactly 1000 chars should be accepted, got {response['statusCode']}"
        
        # Verify CORS headers present
        assert 'Access-Control-Allow-Origin' in response['headers'], \
            "CORS headers must be present in response"


@given(api_gateway_event_with_query(far_over_limit_query_strategy))
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_very_long_query_rejected_with_400(event):
    """
    Property Test: Very long queries (significantly over 1000) are rejected
    
    For any query with length significantly over 1000 characters, the Backend should:
    - Return statusCode 400
    - Include CORS headers
    - Return error message in body
    """
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify 400 status code
        assert response['statusCode'] == 400, \
            f"Expected statusCode 400 for very long query, got {response['statusCode']}"
        
        # Verify CORS headers present
        assert 'Access-Control-Allow-Origin' in response['headers'], \
            "CORS headers must be present in error response"
        
        # Verify error message in body
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain 'error' field"


@given(st.integers(min_value=1001, max_value=10000))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_any_length_over_1000_rejected(query_length):
    """
    Property Test: Any query length > 1000 is consistently rejected
    
    For any integer length > 1000, a query of that length should be rejected with 400.
    This tests the consistency of the length validation logic.
    """
    # Generate a query of exactly the specified length
    query = 'a' * query_length
    
    event = {
        'body': json.dumps({'query': query}),
        'headers': {'Content-Type': 'application/json'},
        'httpMethod': 'POST',
        'path': '/query'
    }
    
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify 400 status code
        assert response['statusCode'] == 400, \
            f"Expected statusCode 400 for query of length {query_length}, got {response['statusCode']}"
        
        # Verify response structure
        assert 'headers' in response, "Response must have headers"
        assert 'body' in response, "Response must have body"
        
        # Verify body is valid JSON
        body = json.loads(response['body'])
        assert isinstance(body, dict), "Response body should be a dictionary"
        assert 'error' in body, "Error response should contain 'error' field"


@given(st.integers(min_value=1, max_value=1000))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_any_length_up_to_1000_accepted(query_length):
    """
    Property Test: Any query length <= 1000 is accepted
    
    For any integer length from 1 to 1000, a query of that length should be accepted
    (not rejected with 400 for length reasons).
    """
    # Generate a query of exactly the specified length (non-whitespace)
    query = 'a' * query_length
    
    event = {
        'body': json.dumps({'query': query}),
        'headers': {'Content-Type': 'application/json'},
        'httpMethod': 'POST',
        'path': '/query'
    }
    
    with patch('boto3.client') as mock_boto3:
        # Mock DynamoDB client
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_dynamodb_response()
        
        # Mock Bedrock client
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = mock_bedrock_response()
        
        def client_side_effect(service, **kwargs):
            if service == 'dynamodb':
                return mock_dynamodb
            elif service == 'bedrock-runtime':
                return mock_bedrock
            return Mock()
        
        mock_boto3.side_effect = client_side_effect
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify NOT 400 (should be accepted)
        assert response['statusCode'] in [200, 500], \
            f"Query of length {query_length} should be accepted, got {response['statusCode']}"


@given(api_gateway_event_with_query(over_limit_query_strategy))
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_cors_headers_in_length_errors(event):
    """
    Property Test: CORS headers present in length validation error responses
    
    For any query length validation error, the response should include proper CORS headers.
    """
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify CORS headers
        assert 'headers' in response, "Response must have headers"
        assert 'Access-Control-Allow-Origin' in response['headers'], \
            "Response must include Access-Control-Allow-Origin header"
        assert response['headers']['Access-Control-Allow-Origin'] == '*', \
            "CORS header should allow all origins"


def test_specific_boundary_cases():
    """
    Test specific boundary cases for query length validation
    
    Tests exact boundary values: 999, 1000, 1001 characters
    """
    test_cases = [
        (999, 'should_accept'),
        (1000, 'should_accept'),
        (1001, 'should_reject'),
        (1002, 'should_reject'),
        (2000, 'should_reject'),
    ]
    
    for length, expected_behavior in test_cases:
        query = 'a' * length
        event = {
            'body': json.dumps({'query': query}),
            'headers': {'Content-Type': 'application/json'},
            'httpMethod': 'POST',
            'path': '/query'
        }
        
        with patch('boto3.client') as mock_boto3:
            if expected_behavior == 'should_accept':
                # Mock DynamoDB and Bedrock for accepted queries
                mock_dynamodb = Mock()
                mock_dynamodb.scan.return_value = mock_dynamodb_response()
                
                mock_bedrock = Mock()
                mock_bedrock.invoke_model.return_value = mock_bedrock_response()
                
                def client_side_effect(service, **kwargs):
                    if service == 'dynamodb':
                        return mock_dynamodb
                    elif service == 'bedrock-runtime':
                        return mock_bedrock
                    return Mock()
                
                mock_boto3.side_effect = client_side_effect
            else:
                # For rejected queries, just mock with basic Mock
                mock_boto3.return_value = Mock()
            
            response = lambda_handler(event, None)
            
            if expected_behavior == 'should_accept':
                assert response['statusCode'] in [200, 500], \
                    f"Query of length {length} should be accepted, got {response['statusCode']}"
            else:
                assert response['statusCode'] == 400, \
                    f"Query of length {length} should be rejected with 400, got {response['statusCode']}"
                
                body = json.loads(response['body'])
                assert 'error' in body, f"Error response for length {length} should contain 'error' field"
    
    print("✓ All specific boundary cases handled correctly")


def test_length_validation_error_message():
    """
    Test that length validation error messages are informative
    
    Validates that error messages clearly indicate the length limit issue.
    """
    # Test with a query over the limit
    query = 'a' * 1500
    event = {
        'body': json.dumps({'query': query}),
        'headers': {'Content-Type': 'application/json'},
        'httpMethod': 'POST',
        'path': '/query'
    }
    
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400, \
            f"Expected 400 for long query, got {response['statusCode']}"
        
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain 'error' field"
        
        error_msg = body['error'].lower()
        # Check that error message is informative about the length issue
        assert any(keyword in error_msg for keyword in ['length', 'maximum', 'exceeds', '1000', 'long']), \
            f"Error message should clearly indicate length issue, got: {body['error']}"
    
    print("✓ Length validation error message is informative")


def run_all_tests():
    """Run all property tests and report results"""
    print("=" * 80)
    print("Property-Based Test: Query Length Limit")
    print("=" * 80)
    print()
    print("**Validates: Requirements 1.3**")
    print()
    print("Property 9: Query Length Limit")
    print("For any query exceeding 1000 characters, the System should reject it.")
    print()
    print("-" * 80)
    
    tests = [
        ("Queries over 1000 chars rejected with 400", test_property_query_over_1000_chars_rejected_with_400),
        ("Queries under 1000 chars accepted", test_property_query_under_1000_chars_accepted),
        ("Queries exactly 1000 chars accepted", test_property_query_exactly_1000_chars_accepted),
        ("Very long queries rejected with 400", test_property_very_long_query_rejected_with_400),
        ("Any length over 1000 rejected", test_property_any_length_over_1000_rejected),
        ("Any length up to 1000 accepted", test_property_any_length_up_to_1000_accepted),
        ("CORS headers in length errors", test_property_cors_headers_in_length_errors),
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
    
    # Run specific test cases
    try:
        print(f"\nRunning: Specific boundary cases...")
        test_specific_boundary_cases()
        print(f"  ✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
        failed += 1
    
    try:
        print(f"\nRunning: Length validation error message...")
        test_length_validation_error_message()
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
        print("  ✓ 1.3 - Queries exceeding 1000 characters are rejected")
        print()
        return 0
    else:
        print()
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
