#!/usr/bin/env python3
"""
Property-Based Test: Query Validation

**Validates: Requirements 1.2, 11.2, 20.5**

Property 3: Query Validation
For any query string that is empty or contains only whitespace, the Backend should 
reject it with a 400 status code, and for any query, whitespace should be trimmed 
before validation.

This test verifies that query validation works correctly, including:
- Empty queries are rejected with 400
- Whitespace-only queries are rejected with 400
- Whitespace is trimmed before validation
- Valid queries after trimming are accepted
- CORS headers are present in all responses
"""

import json
import sys
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings, HealthCheck

# Import the lambda function
sys.path.insert(0, '.')
from lambda_function import lambda_handler


# Strategy for generating empty strings
empty_string_strategy = st.just('')

# Strategy for generating whitespace-only strings
whitespace_only_strategy = st.text(
    alphabet=st.sampled_from([' ', '\t', '\n', '\r', '\f', '\v']),
    min_size=1,
    max_size=50
)

# Strategy for generating strings with leading/trailing whitespace
@st.composite
def string_with_whitespace(draw):
    """Generate a non-empty string with leading and/or trailing whitespace"""
    # Generate core content (non-empty after strip)
    core = draw(st.text(
        alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
        min_size=1,
        max_size=100
    ).filter(lambda x: x.strip() != ''))
    
    # Generate leading whitespace
    leading = draw(st.text(
        alphabet=st.sampled_from([' ', '\t', '\n']),
        min_size=0,
        max_size=10
    ))
    
    # Generate trailing whitespace
    trailing = draw(st.text(
        alphabet=st.sampled_from([' ', '\t', '\n']),
        min_size=0,
        max_size=10
    ))
    
    return leading + core + trailing


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


@given(api_gateway_event_with_query(empty_string_strategy))
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_empty_query_rejected_with_400(event):
    """
    Property Test: Empty queries are rejected with 400
    
    For any empty query string, the Backend should:
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
            f"Expected statusCode 400 for empty query, got {response['statusCode']}"
        
        # Verify CORS headers present
        assert 'Access-Control-Allow-Origin' in response['headers'], \
            "CORS headers must be present in error response"
        
        # Verify error message in body
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain 'error' field"
        assert 'required' in body['error'].lower() or 'empty' in body['error'].lower(), \
            f"Error message should mention query is required or empty, got: {body['error']}"


@given(api_gateway_event_with_query(whitespace_only_strategy))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_whitespace_only_query_rejected_with_400(event):
    """
    Property Test: Whitespace-only queries are rejected with 400
    
    For any query containing only whitespace characters (spaces, tabs, newlines),
    the Backend should:
    - Return statusCode 400
    - Include CORS headers
    - Return error message in body
    
    This validates that whitespace is trimmed before validation.
    """
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify 400 status code
        assert response['statusCode'] == 400, \
            f"Expected statusCode 400 for whitespace-only query, got {response['statusCode']}"
        
        # Verify CORS headers present
        assert 'Access-Control-Allow-Origin' in response['headers'], \
            "CORS headers must be present in error response"
        
        # Verify error message in body
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain 'error' field"


@given(api_gateway_event_with_query(string_with_whitespace()))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_whitespace_trimmed_before_validation(event):
    """
    Property Test: Whitespace is trimmed before validation
    
    For any query with leading or trailing whitespace but non-empty content,
    the Backend should:
    - Trim the whitespace
    - Process the query as valid (if content is valid)
    - Return statusCode 200 or 500 (not 400)
    
    This validates Requirement 20.5: Backend SHALL trim whitespace before checking if empty.
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
        
        # Verify NOT 400 (should be 200 or 500, not rejected for being empty)
        assert response['statusCode'] != 400, \
            f"Query with whitespace but valid content should not return 400, got {response['statusCode']}"
        
        # Should be either 200 (success) or 500 (service error)
        assert response['statusCode'] in [200, 500], \
            f"Expected statusCode 200 or 500 for valid query with whitespace, got {response['statusCode']}"
        
        # Verify CORS headers present
        assert 'Access-Control-Allow-Origin' in response['headers'], \
            "CORS headers must be present in response"


@given(st.one_of(empty_string_strategy, whitespace_only_strategy))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_empty_or_whitespace_always_400(query_value):
    """
    Property Test: Empty or whitespace-only queries always return 400
    
    For any query that is empty or contains only whitespace, the Backend
    should consistently return 400 status code.
    
    This is a combined test for Requirements 1.2 and 20.5.
    """
    event = {
        'body': json.dumps({'query': query_value}),
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
            f"Expected statusCode 400 for empty/whitespace query, got {response['statusCode']}"
        
        # Verify response structure
        assert 'headers' in response, "Response must have headers"
        assert 'body' in response, "Response must have body"
        
        # Verify body is valid JSON
        body = json.loads(response['body'])
        assert isinstance(body, dict), "Response body should be a dictionary"
        assert 'error' in body, "Error response should contain 'error' field"


@given(api_gateway_event_with_query(whitespace_only_strategy))
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_cors_headers_in_validation_errors(event):
    """
    Property Test: CORS headers present in validation error responses
    
    For any query validation error (empty or whitespace-only), the response
    should include proper CORS headers.
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


def test_specific_whitespace_characters():
    """
    Test specific whitespace characters are handled correctly
    
    Tests various whitespace characters: space, tab, newline, carriage return, etc.
    """
    whitespace_chars = [
        ' ',           # space
        '\t',          # tab
        '\n',          # newline
        '\r',          # carriage return
        '\f',          # form feed
        '\v',          # vertical tab
        '   ',         # multiple spaces
        '\t\t',        # multiple tabs
        ' \t\n\r',     # mixed whitespace
    ]
    
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        for ws in whitespace_chars:
            event = {
                'body': json.dumps({'query': ws}),
                'headers': {'Content-Type': 'application/json'},
                'httpMethod': 'POST',
                'path': '/query'
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 400, \
                f"Whitespace '{repr(ws)}' should return 400, got {response['statusCode']}"
            
            body = json.loads(response['body'])
            assert 'error' in body, f"Error response for '{repr(ws)}' should contain 'error' field"
    
    print("✓ All specific whitespace characters handled correctly")


def test_trimming_behavior():
    """
    Test that whitespace trimming works correctly
    
    Validates that queries with leading/trailing whitespace are processed
    after trimming, not rejected.
    """
    test_cases = [
        '  valid query',
        'valid query  ',
        '  valid query  ',
        '\tvalid query',
        'valid query\n',
        '\n\tvalid query\r\n',
    ]
    
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
        
        for query in test_cases:
            event = {
                'body': json.dumps({'query': query}),
                'headers': {'Content-Type': 'application/json'},
                'httpMethod': 'POST',
                'path': '/query'
            }
            
            response = lambda_handler(event, None)
            
            # Should NOT be 400 (should be accepted after trimming)
            assert response['statusCode'] != 400, \
                f"Query '{repr(query)}' should be accepted after trimming, got {response['statusCode']}"
            
            # Should be 200 or 500
            assert response['statusCode'] in [200, 500], \
                f"Query '{repr(query)}' should return 200 or 500, got {response['statusCode']}"
    
    print("✓ Whitespace trimming behavior validated")


def run_all_tests():
    """Run all property tests and report results"""
    print("=" * 80)
    print("Property-Based Test: Query Validation")
    print("=" * 80)
    print()
    print("**Validates: Requirements 1.2, 11.2, 20.5**")
    print()
    print("Property 3: Query Validation")
    print("For any query string that is empty or contains only whitespace, the Backend")
    print("should reject it with a 400 status code, and for any query, whitespace should")
    print("be trimmed before validation.")
    print()
    print("-" * 80)
    
    tests = [
        ("Empty queries rejected with 400", test_property_empty_query_rejected_with_400),
        ("Whitespace-only queries rejected with 400", test_property_whitespace_only_query_rejected_with_400),
        ("Whitespace trimmed before validation", test_property_whitespace_trimmed_before_validation),
        ("Empty or whitespace always returns 400", test_property_empty_or_whitespace_always_400),
        ("CORS headers in validation errors", test_property_cors_headers_in_validation_errors),
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
        print(f"\nRunning: Specific whitespace characters...")
        test_specific_whitespace_characters()
        print(f"  ✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
        failed += 1
    
    try:
        print(f"\nRunning: Trimming behavior...")
        test_trimming_behavior()
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
        print("  ✓ 1.2 - Empty or whitespace-only queries rejected with 400")
        print("  ✓ 11.2 - Backend validates query before processing")
        print("  ✓ 20.5 - Whitespace trimmed before checking if empty")
        print()
        return 0
    else:
        print()
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
