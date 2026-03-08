#!/usr/bin/env python3
"""
Script to create DynamoDB table for AI-Sahayak Government Schemes
Task 1.1: Create DynamoDB table with schema
Requirements: 2.1, 14.4
"""

import boto3
import sys

def create_table():
    """
    Create ai_sahayak_schemes DynamoDB table with:
    - Partition key: scheme_id (String)
    - On-demand billing mode for Free Tier optimization
    """
    try:
        dynamodb = boto3.client('dynamodb')
        
        print("Creating DynamoDB table 'ai_sahayak_schemes'...")
        
        response = dynamodb.create_table(
            TableName='ai_sahayak_schemes',
            KeySchema=[
                {
                    'AttributeName': 'scheme_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'scheme_id',
                    'AttributeType': 'S'  # String
                }
            ],
            BillingMode='PAY_PER_REQUEST',  # On-demand billing for Free Tier
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'AI-Sahayak'
                },
                {
                    'Key': 'Environment',
                    'Value': 'Development'
                }
            ]
        )
        
        print(f"✓ Table creation initiated successfully!")
        print(f"  Table ARN: {response['TableDescription']['TableArn']}")
        print(f"  Table Status: {response['TableDescription']['TableStatus']}")
        print("\nWaiting for table to become active...")
        
        # Wait for table to be created
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName='ai_sahayak_schemes')
        
        print("✓ Table 'ai_sahayak_schemes' is now ACTIVE and ready to use!")
        return True
        
    except dynamodb.exceptions.ResourceInUseException:
        print("⚠ Table 'ai_sahayak_schemes' already exists!")
        return True
    except Exception as e:
        print(f"✗ Error creating table: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_table()
    sys.exit(0 if success else 1)
