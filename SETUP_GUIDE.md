# DynamoDB Setup Guide - Tasks 1.1 & 1.2

## Overview

This guide covers the implementation of Tasks 1.1 and 1.2 from the AI-Sahayak spec:

- **Task 1.1**: Create DynamoDB table with schema
- **Task 1.2**: Seed DynamoDB with initial scheme data

## What Was Created

### 1. `create_dynamodb_table.py`
Python script that creates the `ai_sahayak_schemes` DynamoDB table with:
- **Partition Key**: `scheme_id` (String)
- **Billing Mode**: On-demand (PAY_PER_REQUEST) for Free Tier optimization
- **Tags**: Project and Environment tags for organization
- **Waiter**: Automatically waits for table to become active

**Requirements Validated**: 2.1, 14.4

### 2. `seed_schemes.py`
Python script that seeds the table with 5 sample government schemes:
- Post Matric Scholarship (education)
- PM Kisan (farmer)
- Mudra Loan (business)
- Ayushman Bharat (healthcare)
- PM Awas Yojana (housing)

**Features**:
- Validates all schemes have required fields
- Validates categories are from allowed set
- Provides detailed success/failure feedback
- Verifies insertion by scanning the table

**Requirements Validated**: 2.1, 2.3, 14.1

### 3. `setup_dynamodb.sh`
Bash script that runs both steps in sequence:
- Verifies AWS credentials
- Creates the table
- Seeds with sample data
- Provides clear status messages

### 4. `requirements.txt`
Python dependencies for the scripts:
- boto3 >= 1.34.0 (AWS SDK)
- botocore >= 1.34.0 (Low-level AWS access)

### 5. `README.md`
Comprehensive documentation including:
- Prerequisites
- Step-by-step setup instructions
- Sample scheme details
- Verification commands
- Troubleshooting guide
- AWS Free Tier information

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
cd backend
./setup_dynamodb.sh
```

### Option 2: Manual Step-by-Step

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Step 1: Create table
python3 create_dynamodb_table.py

# Step 2: Seed data
python3 seed_schemes.py
```

## Prerequisites Checklist

Before running the scripts, ensure you have:

- [ ] AWS Account (with Free Tier eligibility)
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Python 3.7 or higher
- [ ] boto3 library installed
- [ ] IAM permissions for DynamoDB operations

## Schema Details

### DynamoDB Table: `ai_sahayak_schemes`

| Field | Type | Description |
|-------|------|-------------|
| scheme_id | String (PK) | Unique identifier (e.g., "SCH001") |
| scheme_name | String | Name of the scheme |
| category | String | One of: education, farmer, business, healthcare, housing |
| description | String | Brief description of the scheme |
| eligibility | String | Eligibility criteria |
| benefits | String | Benefits provided |

### Sample Data

All 5 schemes from the design document are included:

1. **SCH001** - Post Matric Scholarship (education)
2. **SCH002** - PM Kisan (farmer)
3. **SCH003** - Mudra Loan (business)
4. **SCH004** - Ayushman Bharat (healthcare)
5. **SCH005** - PM Awas Yojana (housing)

## Validation

The scripts implement comprehensive validation:

### Table Creation Validation
- ✓ Table name is correct
- ✓ Partition key is configured properly
- ✓ Billing mode is on-demand
- ✓ Table becomes active before proceeding

### Data Seeding Validation
- ✓ All required fields are present
- ✓ Categories are from valid set
- ✓ All 5 schemes are inserted successfully
- ✓ Final count verification

## Cost Considerations

This setup is optimized for AWS Free Tier:

- **DynamoDB Free Tier**: 25 GB storage, 25 read/write capacity units
- **On-demand billing**: Pay only for actual usage
- **Expected cost**: $0 for typical hackathon/demo usage
- **5 schemes**: Minimal storage (~5 KB total)

## Verification Commands

After running the setup, verify with AWS CLI:

```bash
# Check table exists and is active
aws dynamodb describe-table --table-name ai_sahayak_schemes --query 'Table.TableStatus'

# Count items in table
aws dynamodb scan --table-name ai_sahayak_schemes --select COUNT

# View all schemes
aws dynamodb scan --table-name ai_sahayak_schemes

# Get specific scheme
aws dynamodb get-item \
  --table-name ai_sahayak_schemes \
  --key '{"scheme_id": {"S": "SCH001"}}' \
  --query 'Item.scheme_name.S'
```

## Troubleshooting

### Common Issues

**Issue**: "Unable to locate credentials"
```bash
# Solution: Configure AWS CLI
aws configure
```

**Issue**: "Table already exists"
```bash
# Solution: Delete and recreate (if needed)
aws dynamodb delete-table --table-name ai_sahayak_schemes
# Wait 30 seconds, then run create script again
```

**Issue**: "Access Denied"
```bash
# Solution: Ensure IAM user has these permissions:
# - dynamodb:CreateTable
# - dynamodb:PutItem
# - dynamodb:Scan
# - dynamodb:DescribeTable
```

**Issue**: "Region not specified"
```bash
# Solution: Set default region
aws configure set region us-east-1
```

## Requirements Mapping

| Requirement | Description | Validated By |
|-------------|-------------|--------------|
| 2.1 | DynamoDB stores schemes with all required fields | Both scripts |
| 2.3 | Category must be from allowed set | seed_schemes.py |
| 14.1 | System only accepts valid categories | seed_schemes.py |
| 14.4 | DynamoDB schema enforces category field | create_dynamodb_table.py |

## Next Steps

After completing DynamoDB setup:

1. **Create Lambda Function** (Task 1.3+)
   - Implement `lambda_function.py`
   - Configure IAM role with DynamoDB and Bedrock permissions
   - Deploy to AWS Lambda

2. **Set Up API Gateway** (Task 2.x)
   - Create HTTP API
   - Configure POST /query endpoint
   - Enable CORS

3. **Deploy Frontend** (Task 3.x)
   - Host static files (S3 or web server)
   - Update API endpoint URL
   - Test end-to-end flow

## Files Created

```
backend/
├── create_dynamodb_table.py   # Task 1.1 implementation
├── seed_schemes.py             # Task 1.2 implementation
├── setup_dynamodb.sh           # Automated setup script
├── requirements.txt            # Python dependencies
├── README.md                   # User documentation
└── SETUP_GUIDE.md             # This file
```

## Success Criteria

Tasks 1.1 and 1.2 are complete when:

- [x] DynamoDB table `ai_sahayak_schemes` exists
- [x] Table has correct schema (scheme_id as partition key)
- [x] Table uses on-demand billing mode
- [x] 5 sample schemes are inserted
- [x] All schemes have required fields
- [x] All categories are valid
- [x] Scripts include error handling
- [x] Documentation is comprehensive

## Support

If you encounter issues:

1. Check the README.md for detailed instructions
2. Review the troubleshooting section above
3. Verify AWS credentials: `aws sts get-caller-identity`
4. Check AWS region: `aws configure get region`
5. Ensure boto3 is installed: `pip list | grep boto3`

---

**Tasks Completed**: 1.1 ✓, 1.2 ✓
