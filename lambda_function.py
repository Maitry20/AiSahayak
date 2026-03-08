"""
AI-Sahayak Lambda Function
Government Schemes Assistant Backend

This Lambda function processes user queries about government schemes,
retrieves scheme data from DynamoDB, and generates AI responses using Amazon Bedrock.
"""

import json
import boto3
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (reused across invocations)
dynamodb_client = None
bedrock_client = None


def get_cors_headers() -> Dict[str, str]:
    """
    Return CORS headers for all responses
    
    Returns:
        Dictionary with CORS headers
    """
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a properly formatted API Gateway response
    
    Args:
        status_code: HTTP status code
        body: Response body dictionary
        
    Returns:
        API Gateway response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(body)
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function
    
    Args:
        event: API Gateway event containing request body
        context: Lambda context object
        
    Returns:
        API Gateway response with statusCode, headers, and body
    """
    global dynamodb_client, bedrock_client
    
    try:
        # Initialize clients if not already done
        if dynamodb_client is None:
            dynamodb_client = boto3.client('dynamodb')
        if bedrock_client is None:
            bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return create_response(400, {'error': 'Invalid request format'})
        
        # Extract and validate query
        query = body.get('query', '').strip()
        
        if not query:
            logger.info("Empty query received")
            return create_response(400, {'error': 'Query is required'})
        
        if len(query) > 1000:
            logger.info(f"Query too long: {len(query)} characters")
            return create_response(400, {'error': 'Query exceeds maximum length of 1000 characters'})
        
        # Retrieve schemes from DynamoDB
        try:
            schemes = get_all_schemes(dynamodb_client)
            logger.info(f"Retrieved {len(schemes)} schemes from DynamoDB")
        except Exception as e:
            logger.error(f"DynamoDB error: {str(e)}")
            return create_response(500, {'error': 'Failed to retrieve scheme data'})
        
        # Build context from schemes
        context_text = build_context(schemes)
        
        # Invoke Bedrock for AI response
        try:
            ai_response = invoke_bedrock(query, context_text, bedrock_client)
            logger.info("Successfully generated AI response")
        except Exception as e:
            logger.error(f"Bedrock error: {str(e)}")
            return create_response(500, {'error': 'AI service temporarily unavailable'})
        
        # Return success response
        return create_response(200, {'response': ai_response})
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def get_all_schemes(dynamodb_client) -> List[Dict[str, Any]]:
    """
    Retrieve all schemes from DynamoDB
    
    Args:
        dynamodb_client: Boto3 DynamoDB client
        
    Returns:
        List of scheme dictionaries
        
    Raises:
        Exception: If DynamoDB access fails
    """
    table_name = 'ai_sahayak_schemes'
    schemes = []
    
    try:
        response = dynamodb_client.scan(TableName=table_name)
        items = response.get('Items', [])
        
        for item in items:
            scheme = {
                'scheme_id': item['scheme_id']['S'],
                'scheme_name': item['scheme_name']['S'],
                'category': item['category']['S'],
                'description': item['description']['S'],
                'eligibility': item['eligibility']['S'],
                'benefits': item['benefits']['S']
            }
            schemes.append(scheme)
        
        return schemes
        
    except Exception as e:
        raise Exception(f"Failed to retrieve schemes: {str(e)}")


def build_context(schemes: List[Dict[str, Any]]) -> str:
    """
    Convert schemes list into formatted text context
    
    Args:
        schemes: List of scheme dictionaries
        
    Returns:
        Formatted string containing all scheme information
    """
    if not schemes:
        return "No schemes available in database."
    
    context_parts = []
    
    for scheme in schemes:
        scheme_text = f"""
Scheme: {scheme['scheme_name']}
Category: {scheme['category']}
Description: {scheme['description']}
Eligibility: {scheme['eligibility']}
Benefits: {scheme['benefits']}
---"""
        context_parts.append(scheme_text)
    
    return "\n".join(context_parts)


def invoke_bedrock(query: str, context: str, bedrock_client) -> str:
    """
    Call Amazon Bedrock model with prompt
    
    Args:
        query: User's question
        context: Formatted scheme information
        bedrock_client: Boto3 Bedrock client
        
    Returns:
        AI-generated response text
        
    Raises:
        Exception: If Bedrock invocation fails
    """
    prompt = f"""You are AI-Sahayak, a digital assistant helping Indian citizens understand government schemes.

User Question: {query}

Available Schemes:
{context}

Instructions:
- Identify the most relevant scheme(s) for the user's question
- Explain in simple, clear language
- If the question is in Hindi or Gujarati, respond in the same language
- Be helpful and concise

Response:"""
    
    request_body = {
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 500,
            "temperature": 0.7
        }
    }
    
    try:
        response = bedrock_client.invoke_model(
            modelId='amazon.nova-lite-v1:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        ai_text = response_body['output']['message']['content'][0]['text']
        
        return ai_text.strip()
        
    except Exception as e:
        raise Exception(f"Bedrock invocation failed: {str(e)}")
