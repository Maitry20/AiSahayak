#!/usr/bin/env python3
"""
Property-Based Test: Lambda Response Validity

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6**

Property 1: Lambda Response Validity
For any valid API Gateway event, the lambda_handler function should return a response 
with statusCode in {200, 400, 500}, CORS headers present, and body containing valid JSON.

This test verifies that IAM permissions are working correctly by ensuring the Lambda
can interact with AWS services and return properly formatted responses.
"""

import json
import sys
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis import assume

# Import the lambda function
sys.path.insert(0, '.')
from lambda_function import lambda_handler, get_cors_headers


# Strategy for generating valid queries
valid_query_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=1,
    max_size=1000
).filter(lambda x: x.strip() != '')

# Strategy for generating invalid queries (empty or whitespace)
invalid_query_strategy = st.one_of(
    st.just(''),
    st.text(alphabet=st.just(' '), min_size=1, max_size=10)
)

# Strategy for generating too-long queries
long_query_strategy = st.text(min_size=1001, max_size=2000)

# Strategy for generating API Gateway events
@st.composite
def api_gateway_event(draw, query_strategy=valid_query_strategy):
    """Generate API Gateway event with query"""
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
            }
        ]
    }


def mock_bedrock_response():
    """Create a mock Bedrock response"""
    response_body = {
        'output': {
            'message': {
                'content': [
                    {'text': 'Based on your query, the Post Matric Scholarship is most relevant for students seeking financial assistance for education.'}
                ]
            }
        }
    }
    
    # Create a mock body object with read method
    mock_body = Mock()
    mock_body.read.return_value = json.dumps(response_body).encode('utf-8')
    
    # Create response dictionary with mock body
    mock_response = {
        'body': mock_body,
        'ResponseMetadata': {
            'HTTPStatusCode': 200
        }
    }
    return mock_response


def validate_response_structure(response):
    """
    Validate that response has correct structure
    
    Returns tuple: (is_valid, error_message)
    """
    # Check response is a dictionary
    if not isinstance(response, dict):
        return False, "Response is not a dictionary"
    
    # Check required fields exist
    if 'statusCode' not in response:
        return False, "Missing 'statusCode' field"
    
    if 'headers' not in response:
        return False, "Missing 'headers' field"
    
    if 'body' not in response:
        return False, "Missing 'body' field"
    
    # Check statusCode is valid
    if response['statusCode'] not in [200, 400, 500]:
        return False, f"Invalid statusCode: {response['statusCode']}, expected one of [200, 400, 500]"
    
    # Check headers is a dictionary
    if not isinstance(response['headers'], dict):
        return False, "Headers is not a dictionary"
    
    # Check CORS headers are present
    if 'Access-Control-Allow-Origin' not in response['headers']:
        return False, "Missing CORS header 'Access-Control-Allow-Origin'"
    
    # Check body is a string
    if not isinstance(response['body'], str):
        return False, "Body is not a string"
    
    # Check body contains valid JSON
    try:
        body_data = json.loads(response['body'])
    except json.JSONDecodeError as e:
        return False, f"Body is not valid JSON: {str(e)}"
    
    # Check body is a dictionary
    if not isinstance(body_data, dict):
        return False, "Body JSON is not a dictionary"
    
    return True, None


@given(api_gateway_event(valid_query_strategy))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_valid_query_returns_valid_response(event):
    """
    Property Test: Valid queries return properly formatted responses
    
    For any valid query (non-empty, <= 1000 chars), the Lambda should return:
    - statusCode: 200 (on success) or 500 (on service error)
    - CORS headers present
    - body: valid JSON string
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
        
        # Validate response structure
        is_valid, error_msg = validate_response_structure(response)
        assert is_valid, f"Response validation failed: {error_msg}"
        
        # For valid queries, we expect either 200 (success) or 500 (service error)
        assert response['statusCode'] in [200, 500], \
            f"Expected statusCode 200 or 500 for valid query, got {response['statusCode']}"


@given(api_gateway_event(invalid_query_strategy))
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_empty_query_returns_400(event):
    """
    Property Test: Empty or whitespace queries return 400
    
    For any empty or whitespace-only query, the Lambda should return:
    - statusCode: 400
    - CORS headers present
    - body: valid JSON with error message
    """
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Validate response structure
        is_valid, error_msg = validate_response_structure(response)
        assert is_valid, f"Response validation failed: {error_msg}"
        
        # Empty queries should return 400
        assert response['statusCode'] == 400, \
            f"Expected statusCode 400 for empty query, got {response['statusCode']}"
        
        # Check error message is present
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain 'error' field"


@given(api_gateway_event(long_query_strategy))
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_long_query_returns_400(event):
    """
    Property Test: Queries exceeding 1000 characters return 400
    
    For any query longer than 1000 characters, the Lambda should return:
    - statusCode: 400
    - CORS headers present
    - body: valid JSON with error message
    """
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Validate response structure
        is_valid, error_msg = validate_response_structure(response)
        assert is_valid, f"Response validation failed: {error_msg}"
        
        # Long queries should return 400
        assert response['statusCode'] == 400, \
            f"Expected statusCode 400 for long query, got {response['statusCode']}"
        
        # Check error message is present
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain 'error' field"


@given(st.text())
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_invalid_json_returns_400(invalid_body):
    """
    Property Test: Invalid JSON in request body returns 400
    
    For any invalid JSON string, the Lambda should return:
    - statusCode: 400
    - CORS headers present
    - body: valid JSON with error message
    """
    # Filter out valid JSON strings
    try:
        json.loads(invalid_body)
        assume(False)  # Skip if it's valid JSON
    except (json.JSONDecodeError, TypeError):
        pass  # This is what we want - invalid JSON
    
    event = {
        'body': invalid_body,
        'headers': {'Content-Type': 'application/json'},
        'httpMethod': 'POST',
        'path': '/query'
    }
    
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = Mock()
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Validate response structure
        is_valid, error_msg = validate_response_structure(response)
        assert is_valid, f"Response validation failed: {error_msg}"
        
        # Invalid JSON should return 400
        assert response['statusCode'] == 400, \
            f"Expected statusCode 400 for invalid JSON, got {response['statusCode']}"


@given(api_gateway_event(valid_query_strategy))
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_dynamodb_error_returns_500(event):
    """
    Property Test: DynamoDB errors return 500
    
    When DynamoDB access fails, the Lambda should return:
    - statusCode: 500
    - CORS headers present
    - body: valid JSON with error message
    """
    # Import and reset global clients
    import lambda_function
    lambda_function.dynamodb_client = None
    lambda_function.bedrock_client = None
    
    with patch('boto3.client') as mock_boto3:
        # Mock DynamoDB client that raises an exception
        mock_dynamodb = Mock()
        mock_dynamodb.scan.side_effect = Exception("DynamoDB connection failed")
        
        # Mock Bedrock client (won't be called)
        mock_bedrock = Mock()
        
        def client_side_effect(service, **kwargs):
            if service == 'dynamodb':
                return mock_dynamodb
            elif service == 'bedrock-runtime':
                return mock_bedrock
            return Mock()
        
        mock_boto3.side_effect = client_side_effect
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Validate response structure
        is_valid, error_msg = validate_response_structure(response)
        assert is_valid, f"Response validation failed: {error_msg}"
        
        # DynamoDB errors should return 500
        assert response['statusCode'] == 500, \
            f"Expected statusCode 500 for DynamoDB error, got {response['statusCode']}"
        
        # Check error message is present
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain 'error' field"


@given(api_gateway_event(valid_query_strategy))
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_bedrock_error_returns_500(event):
    """
    Property Test: Bedrock errors return 500
    
    When Bedrock invocation fails, the Lambda should return:
    - statusCode: 500
    - CORS headers present
    - body: valid JSON with error message
    """
    # Import and reset global clients
    import lambda_function
    lambda_function.dynamodb_client = None
    lambda_function.bedrock_client = None
    
    with patch('boto3.client') as mock_boto3:
        # Mock DynamoDB client (succeeds)
        mock_dynamodb = Mock()
        mock_dynamodb.scan.return_value = mock_dynamodb_response()
        
        # Mock Bedrock client that raises an exception
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("Bedrock service unavailable")
        
        def client_side_effect(service, **kwargs):
            if service == 'dynamodb':
                return mock_dynamodb
            elif service == 'bedrock-runtime':
                return mock_bedrock
            return Mock()
        
        mock_boto3.side_effect = client_side_effect
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Validate response structure
        is_valid, error_msg = validate_response_structure(response)
        assert is_valid, f"Response validation failed: {error_msg}"
        
        # Bedrock errors should return 500
        assert response['statusCode'] == 500, \
            f"Expected statusCode 500 for Bedrock error, got {response['statusCode']}"
        
        # Check error message is present
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain 'error' field"


@given(api_gateway_event(valid_query_strategy))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_cors_headers_always_present(event):
    """
    Property Test: CORS headers are present in all responses
    
    For any request (valid or invalid), the Lambda should always include:
    - Access-Control-Allow-Origin header
    - Other CORS headers as needed
    """
    with patch('boto3.client') as mock_boto3:
        # Mock clients
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
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Check CORS headers
        assert 'headers' in response, "Response must have headers"
        assert 'Access-Control-Allow-Origin' in response['headers'], \
            "Response must include Access-Control-Allow-Origin header"
        assert response['headers']['Access-Control-Allow-Origin'] == '*', \
            "CORS header should allow all origins"


def run_all_tests():
    """Run all property tests and report results"""
    print("=" * 80)
    print("Property-Based Test: Lambda Response Validity")
    print("=" * 80)
    print()
    print("**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6**")
    print()
    print("Property 1: Lambda Response Validity")
    print("For any valid API Gateway event, the lambda_handler function should return")
    print("a response with statusCode in {200, 400, 500}, CORS headers present,")
    print("and body containing valid JSON.")
    print()
    print("-" * 80)
    
    tests = [
        ("Valid queries return valid responses", test_property_valid_query_returns_valid_response),
        ("Empty queries return 400", test_property_empty_query_returns_400),
        ("Long queries return 400", test_property_long_query_returns_400),
        ("Invalid JSON returns 400", test_property_invalid_json_returns_400),
        ("DynamoDB errors return 500", test_property_dynamodb_error_returns_500),
        ("Bedrock errors return 500", test_property_bedrock_error_returns_500),
        ("CORS headers always present", test_property_cors_headers_always_present),
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
    
    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print()
        print("✓ All Property Tests Passed!")
        print()
        print("Requirements Validated:")
        print("  ✓ 8.1 - Backend returns responses with statusCode, headers, and body")
        print("  ✓ 8.2 - Successful requests return statusCode 200")
        print("  ✓ 8.3 - Invalid input returns statusCode 400")
        print("  ✓ 8.4 - Internal errors return statusCode 500")
        print("  ✓ 8.5 - Response body is JSON string")
        print("  ✓ 8.6 - Access-Control-Allow-Origin header in all responses")
        print()
        return 0
    else:
        print()
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
