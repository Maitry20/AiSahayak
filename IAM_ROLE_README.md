# Lambda IAM Role - Quick Reference

## Task 2.1: Create Lambda Execution Role

### Quick Setup

```bash
cd backend
./setup_iam_role.sh
```

### What Gets Created

**Role Name**: `ai-sahayak-lambda-role`

**Permissions**:
- ✓ DynamoDB: Scan and GetItem on `ai_sahayak_schemes` table
- ✓ Bedrock: InvokeModel on `amazon.nova-lite-v1` model
- ✓ CloudWatch Logs: Full logging access

### Files

| File | Purpose |
|------|---------|
| `iam_trust_policy.json` | Allows Lambda to assume the role |
| `iam_permissions_policy.json` | Grants DynamoDB, Bedrock, and CloudWatch access |
| `create_iam_role.py` | Python script to create the role |
| `setup_iam_role.sh` | Automated setup script |
| `IAM_ROLE_GUIDE.md` | Comprehensive documentation |

### Get Role ARN

After creation, get your role ARN:

```bash
aws iam get-role \
  --role-name ai-sahayak-lambda-role \
  --query 'Role.Arn' \
  --output text
```

You'll need this ARN when creating the Lambda function in Task 10.2.

### Requirements

- AWS CLI configured (`aws configure`)
- Python 3.7+
- boto3 installed (`pip install boto3`)
- IAM permissions to create roles

### Troubleshooting

**No AWS credentials?**
```bash
aws configure
```

**Role already exists?**
The script handles this automatically - it will use the existing role.

**Need to delete and recreate?**
```bash
aws iam delete-role-policy \
  --role-name ai-sahayak-lambda-role \
  --policy-name ai-sahayak-lambda-policy

aws iam delete-role --role-name ai-sahayak-lambda-role
```

### Next Steps

1. Save the role ARN from the output
2. Proceed to Task 3.1: Implement Lambda function
3. Use this role when deploying Lambda in Task 10.2

---

**Requirements Validated**: 11.1, 15.6
