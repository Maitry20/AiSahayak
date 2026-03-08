#!/usr/bin/env python3
"""
Create IAM role for AI-Sahayak Lambda function

This script creates the Lambda execution role with permissions for:
- DynamoDB read access (Scan, GetItem)
- Bedrock InvokeModel access
- CloudWatch Logs access

Requirements: 11.1, 15.6
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

# Configuration
ROLE_NAME = "ai-sahayak-lambda-role"
POLICY_NAME = "ai-sahayak-lambda-policy"
TRUST_POLICY_FILE = "iam_trust_policy.json"
PERMISSIONS_POLICY_FILE = "iam_permissions_policy.json"


def load_policy_document(filename):
    """Load policy document from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Policy file '{filename}' not found")
        raise
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in '{filename}'")
        raise


def create_iam_role(iam_client):
    """Create IAM role with trust policy for Lambda service"""
    print(f"Creating IAM role: {ROLE_NAME}")
    
    # Load trust policy
    trust_policy = load_policy_document(TRUST_POLICY_FILE)
    
    try:
        response = iam_client.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for AI-Sahayak Lambda function",
            Tags=[
                {'Key': 'Project', 'Value': 'AI-Sahayak'},
                {'Key': 'Environment', 'Value': 'Development'}
            ]
        )
        
        role_arn = response['Role']['Arn']
        print(f"✓ IAM role created successfully")
        print(f"  Role ARN: {role_arn}")
        return role_arn
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"⚠ Role '{ROLE_NAME}' already exists")
            # Get existing role ARN
            response = iam_client.get_role(RoleName=ROLE_NAME)
            role_arn = response['Role']['Arn']
            print(f"  Using existing role ARN: {role_arn}")
            return role_arn
        else:
            print(f"❌ Error creating role: {e}")
            raise


def attach_inline_policy(iam_client):
    """Attach inline policy with DynamoDB, Bedrock, and CloudWatch permissions"""
    print(f"\nAttaching permissions policy: {POLICY_NAME}")
    
    # Load permissions policy
    permissions_policy = load_policy_document(PERMISSIONS_POLICY_FILE)
    
    try:
        iam_client.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName=POLICY_NAME,
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        print(f"✓ Permissions policy attached successfully")
        print(f"  Policy includes:")
        print(f"    - DynamoDB: Scan, GetItem on ai_sahayak_schemes table")
        print(f"    - Bedrock: InvokeModel on amazon.nova-lite-v1")
        print(f"    - CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents")
        
    except ClientError as e:
        print(f"❌ Error attaching policy: {e}")
        raise


def verify_role_setup(iam_client):
    """Verify the role and policy are properly configured"""
    print(f"\nVerifying role setup...")
    
    try:
        # Get role details
        role_response = iam_client.get_role(RoleName=ROLE_NAME)
        role_arn = role_response['Role']['Arn']
        
        # Get attached inline policies
        policies_response = iam_client.list_role_policies(RoleName=ROLE_NAME)
        inline_policies = policies_response['PolicyNames']
        
        print(f"✓ Role verification complete")
        print(f"  Role Name: {ROLE_NAME}")
        print(f"  Role ARN: {role_arn}")
        print(f"  Inline Policies: {', '.join(inline_policies)}")
        
        return role_arn
        
    except ClientError as e:
        print(f"❌ Error verifying role: {e}")
        raise


def main():
    """Main execution function"""
    print("=" * 70)
    print("AI-Sahayak Lambda IAM Role Setup")
    print("Task 2.1: Create Lambda execution role")
    print("=" * 70)
    print()
    
    try:
        # Initialize IAM client
        iam_client = boto3.client('iam')
        print("✓ IAM client initialized")
        print()
        
        # Step 1: Create IAM role
        role_arn = create_iam_role(iam_client)
        
        # Step 2: Attach permissions policy
        attach_inline_policy(iam_client)
        
        # Wait a moment for IAM to propagate
        print("\nWaiting for IAM changes to propagate...")
        time.sleep(2)
        
        # Step 3: Verify setup
        final_role_arn = verify_role_setup(iam_client)
        
        # Success summary
        print()
        print("=" * 70)
        print("✓ IAM Role Setup Complete!")
        print("=" * 70)
        print()
        print("Next Steps:")
        print("1. Use this role ARN when creating the Lambda function:")
        print(f"   {final_role_arn}")
        print()
        print("2. The role has the following permissions:")
        print("   - Read access to DynamoDB table 'ai_sahayak_schemes'")
        print("   - Invoke access to Bedrock model 'amazon.nova-lite-v1'")
        print("   - Write access to CloudWatch Logs")
        print()
        print("3. Proceed to Task 3.1: Implement Lambda function")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Setup Failed")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Ensure AWS credentials are configured: aws configure")
        print("2. Verify IAM permissions to create roles and policies")
        print("3. Check that policy JSON files exist in the current directory")
        print("4. Review AWS IAM documentation for role creation")
        print()
        return 1


if __name__ == "__main__":
    exit(main())
