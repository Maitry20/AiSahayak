# IAM Role Setup Guide - Task 2.1

## Overview

This guide covers the implementation of Task 2.1 from the AI-Sahayak spec:

- **Task 2.1**: Create Lambda execution role with appropriate permissions

## What Was Created

### 1. `iam_trust_policy.json`
Trust policy document that allows Lambda service to assume the role:
- Grants `sts:AssumeRole` permission to `lambda.amazonaws.com`
- Required for Lambda to execute with this role

### 2. `iam_permissions_policy.json`
Permissions policy document with three key access grants:

**DynamoDB Access**:
- `dynamodb:Scan` - Retrieve all schemes from the table
- `dynamodb:GetItem` - Get individual scheme items
- Resource: `ai_sahayak_schemes` table

**Bedrock Access**:
- `bedrock:InvokeModel` - Call the AI model
- Resource: `amazon.nova-lite-v1:0` model in us-east-1

**CloudWatch Logs Access**:
- `logs:CreateLogGroup` - Create log groups
- `logs:CreateLogStream` - Create log streams
- `logs:PutLogEvents` - Write log events
- Resource: All CloudWatch Logs resources

**Requirements Validated**: 11.1, 15.6

### 3. `create_iam_role.py`
Python script that:
- Creates IAM role named `ai-sahayak-lambda-role`
- Attaches trust policy for Lambda service
- Attaches inline permissions policy
- Handles existing role gracefully
- Verifies role setup
- Provides detailed status output

**Features**:
- Comprehensive error handling
- Idempotent (can run multiple times safely)
- Detailed verification output
- Tags for organization

### 4. `setup_iam_role.sh`
Bash script that:
- Verifies AWS credentials
- Checks Python and boto3 installation
- Validates policy files exist
- Runs the Python script
- Provides clear status messages

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
cd backend
./setup_iam_role.sh
```

### Option 2: Manual Step-by-Step

```bash
cd backend

# Ensure boto3 is installed
pip install boto3

# Create the IAM role
python3 create_iam_role.py
```

### Option 3: Using AWS CLI

```bash
cd backend

# Create the role
aws iam create-role \
  --role-name ai-sahayak-lambda-role \
  --assume-role-policy-document file://iam_trust_policy.json \
  --description "Execution role for AI-Sahayak Lambda function"

# Attach the permissions policy
aws iam put-role-policy \
  --role-name ai-sahayak-lambda-role \
  --policy-name ai-sahayak-lambda-policy \
  --policy-document file://iam_permissions_policy.json

# Get the role ARN
aws iam get-role \
  --role-name ai-sahayak-lambda-role \
  --query 'Role.Arn' \
  --output text
```

## Prerequisites Checklist

Before running the scripts, ensure you have:

- [ ] AWS Account with IAM permissions
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Python 3.7 or higher
- [ ] boto3 library installed
- [ ] IAM permissions to create roles and policies

## IAM Permissions Required

Your AWS user/role needs these IAM permissions to run the setup:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:GetRole",
        "iam:PutRolePolicy",
        "iam:ListRolePolicies",
        "iam:TagRole"
      ],
      "Resource": "arn:aws:iam::*:role/ai-sahayak-lambda-role"
    }
  ]
}
```

## Role Details

### Role Name
`ai-sahayak-lambda-role`

### Role ARN Format
`arn:aws:iam::{ACCOUNT_ID}:role/ai-sahayak-lambda-role`

### Trust Policy
Allows Lambda service to assume this role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Permissions Policy
Three main permission sets:

1. **DynamoDB Read Access**
   - Actions: `Scan`, `GetItem`
   - Resource: `ai_sahayak_schemes` table
   - Purpose: Retrieve government scheme data

2. **Bedrock Invoke Access**
   - Action: `InvokeModel`
   - Resource: `amazon.nova-lite-v1:0` model
   - Purpose: Generate AI responses

3. **CloudWatch Logs Access**
   - Actions: `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`
   - Resource: All logs
   - Purpose: Application logging and monitoring

## Security Best Practices

This IAM role follows the principle of least privilege:

✓ **Minimal Permissions**: Only grants necessary actions
✓ **Resource Restrictions**: Scoped to specific DynamoDB table and Bedrock model
✓ **No Write Access**: DynamoDB permissions are read-only
✓ **Service-Specific**: Trust policy limited to Lambda service
✓ **No Wildcard Actions**: All actions explicitly listed

## Verification Commands

After running the setup, verify with AWS CLI:

```bash
# Check role exists
aws iam get-role --role-name ai-sahayak-lambda-role

# Get role ARN
aws iam get-role \
  --role-name ai-sahayak-lambda-role \
  --query 'Role.Arn' \
  --output text

# List attached inline policies
aws iam list-role-policies --role-name ai-sahayak-lambda-role

# View the permissions policy
aws iam get-role-policy \
  --role-name ai-sahayak-lambda-role \
  --policy-name ai-sahayak-lambda-policy
```

## Using the Role with Lambda

When creating your Lambda function, use the role ARN:

### AWS Console
1. Go to Lambda → Create function
2. Under "Permissions", select "Use an existing role"
3. Choose `ai-sahayak-lambda-role`

### AWS CLI
```bash
aws lambda create-function \
  --function-name ai-sahayak-backend \
  --runtime python3.12 \
  --role arn:aws:iam::{ACCOUNT_ID}:role/ai-sahayak-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip
```

### Python (boto3)
```python
import boto3

lambda_client = boto3.client('lambda')

response = lambda_client.create_function(
    FunctionName='ai-sahayak-backend',
    Runtime='python3.12',
    Role='arn:aws:iam::{ACCOUNT_ID}:role/ai-sahayak-lambda-role',
    Handler='lambda_function.lambda_handler',
    Code={'ZipFile': open('function.zip', 'rb').read()}
)
```

## Troubleshooting

### Common Issues

**Issue**: "Unable to locate credentials"
```bash
# Solution: Configure AWS CLI
aws configure
```

**Issue**: "User is not authorized to perform: iam:CreateRole"
```bash
# Solution: Your AWS user needs IAM permissions
# Contact your AWS administrator or use an account with IAM access
```

**Issue**: "Role already exists"
```bash
# Solution: The script handles this automatically
# If you need to recreate, delete the role first:
aws iam delete-role-policy \
  --role-name ai-sahayak-lambda-role \
  --policy-name ai-sahayak-lambda-policy

aws iam delete-role --role-name ai-sahayak-lambda-role

# Then run the setup script again
```

**Issue**: "Policy file not found"
```bash
# Solution: Ensure you're in the backend directory
cd backend
ls -la iam_*.json

# Files should be present:
# - iam_trust_policy.json
# - iam_permissions_policy.json
```

**Issue**: "Access denied for bedrock:InvokeModel"
```bash
# Solution: Ensure Bedrock is enabled in your AWS account
# 1. Go to AWS Console → Bedrock
# 2. Request model access for amazon.nova-lite-v1
# 3. Wait for approval (usually instant for nova-lite)
```

## Cost Considerations

IAM roles are **free** in AWS:
- No charge for creating roles
- No charge for attaching policies
- No charge for role assumptions

The costs come from the services the role accesses:
- **DynamoDB**: Free Tier covers typical usage
- **Bedrock**: Pay per token (nova-lite is cost-effective)
- **CloudWatch Logs**: Free Tier covers 5GB/month

## Requirements Mapping

| Requirement | Description | Validated By |
|-------------|-------------|--------------|
| 11.1 | Lambda SHALL have IAM permissions limited to DynamoDB Scan/GetItem, Bedrock InvokeModel, and CloudWatch Logs | iam_permissions_policy.json |
| 15.6 | Backend SHALL use boto3 clients for AWS service interactions | create_iam_role.py |

## Next Steps

After completing IAM role setup:

1. **Save the Role ARN** - You'll need it for Lambda creation
   ```bash
   aws iam get-role \
     --role-name ai-sahayak-lambda-role \
     --query 'Role.Arn' \
     --output text
   ```

2. **Proceed to Task 3.1** - Implement Lambda function
   - Create `lambda_function.py`
   - Implement handler and helper functions
   - Use boto3 clients for DynamoDB and Bedrock

3. **Deploy Lambda** (Task 10.x)
   - Package the function
   - Deploy with the IAM role
   - Test with sample events

## Files Created

```
backend/
├── iam_trust_policy.json          # Trust policy for Lambda service
├── iam_permissions_policy.json    # Permissions for DynamoDB, Bedrock, CloudWatch
├── create_iam_role.py             # Python script to create role
├── setup_iam_role.sh              # Automated setup script
└── IAM_ROLE_GUIDE.md              # This file
```

## Success Criteria

Task 2.1 is complete when:

- [x] IAM role `ai-sahayak-lambda-role` exists
- [x] Trust policy allows Lambda service to assume role
- [x] Permissions policy grants DynamoDB Scan and GetItem
- [x] Permissions policy grants Bedrock InvokeModel
- [x] Permissions policy grants CloudWatch Logs access
- [x] Role follows principle of least privilege
- [x] Scripts include error handling
- [x] Documentation is comprehensive

## Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Verify AWS credentials: `aws sts get-caller-identity`
3. Check IAM permissions: `aws iam get-user`
4. Review AWS IAM documentation
5. Check CloudWatch Logs for Lambda execution errors (after deployment)

---

**Task Completed**: 2.1 ✓

**Role ARN**: Run `aws iam get-role --role-name ai-sahayak-lambda-role --query 'Role.Arn' --output text` to get your role ARN.
