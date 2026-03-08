# AI-Sahayak Backend Setup

This directory contains scripts to set up the DynamoDB infrastructure for the AI-Sahayak Government Schemes application.

## Prerequisites

1. **AWS Account**: You need an active AWS account
2. **AWS CLI**: Install and configure AWS CLI with your credentials
   ```bash
   aws configure
   ```
   You'll need to provide:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., `us-east-1`)
   - Default output format (e.g., `json`)

3. **Python 3**: Python 3.7 or higher
4. **boto3**: AWS SDK for Python
   ```bash
   pip install boto3
   ```

## Setup Instructions

### Step 1: Create DynamoDB Table

Run the table creation script:

```bash
python3 create_dynamodb_table.py
```

This script will:
- Create a DynamoDB table named `ai_sahayak_schemes`
- Configure it with partition key `scheme_id` (String)
- Set billing mode to on-demand (PAY_PER_REQUEST) for Free Tier optimization
- Wait for the table to become active

**Expected Output:**
```
Creating DynamoDB table 'ai_sahayak_schemes'...
✓ Table creation initiated successfully!
  Table ARN: arn:aws:dynamodb:us-east-1:123456789012:table/ai_sahayak_schemes
  Table Status: CREATING

Waiting for table to become active...
✓ Table 'ai_sahayak_schemes' is now ACTIVE and ready to use!
```

### Step 2: Seed with Sample Data

Run the seeding script:

```bash
python3 seed_schemes.py
```

This script will:
- Insert 5 sample government schemes into the table
- Validate each scheme has all required fields
- Verify categories are valid (education, farmer, business, healthcare, housing)
- Confirm successful insertion

**Expected Output:**
```
Seeding DynamoDB table 'ai_sahayak_schemes' with 5 schemes...

✓ Inserted: Post Matric Scholarship (education)
✓ Inserted: PM Kisan (farmer)
✓ Inserted: Mudra Loan (business)
✓ Inserted: Ayushman Bharat (healthcare)
✓ Inserted: PM Awas Yojana (housing)

✓ Successfully seeded 5/5 schemes!

Verifying inserted schemes...
✓ Table now contains 5 schemes
```

## Sample Schemes

The following 5 schemes are inserted:

1. **Post Matric Scholarship** (education)
   - For students from economically weaker sections
   - Family income below 2.5 lakh
   - Covers tuition fees and maintenance allowance

2. **PM Kisan** (farmer)
   - Income support for farmers
   - All landholding farmers eligible
   - Rs 6000 per year in three installments

3. **Mudra Loan** (business)
   - Loans for micro and small enterprises
   - Non-corporate, non-farm small/micro enterprises
   - Loans up to Rs 10 lakh

4. **Ayushman Bharat** (healthcare)
   - Health insurance for economically vulnerable families
   - Families identified through SECC database
   - Health cover of Rs 5 lakh per family per year

5. **PM Awas Yojana** (housing)
   - Affordable housing for urban poor
   - EWS/LIG families without pucca house
   - Financial assistance for house construction

## Verification

To verify the table and data were created successfully, you can use AWS CLI:

```bash
# Check table status
aws dynamodb describe-table --table-name ai_sahayak_schemes

# View all schemes
aws dynamodb scan --table-name ai_sahayak_schemes

# Get a specific scheme
aws dynamodb get-item --table-name ai_sahayak_schemes --key '{"scheme_id": {"S": "SCH001"}}'
```

## Troubleshooting

### Error: "Unable to locate credentials"
- Run `aws configure` to set up your AWS credentials
- Ensure your IAM user has DynamoDB permissions

### Error: "Table already exists"
- The table was already created. You can proceed to seeding.
- To recreate, delete the table first:
  ```bash
  aws dynamodb delete-table --table-name ai_sahayak_schemes
  ```

### Error: "Access Denied"
- Ensure your IAM user has the following permissions:
  - `dynamodb:CreateTable`
  - `dynamodb:PutItem`
  - `dynamodb:Scan`
  - `dynamodb:DescribeTable`

## AWS Free Tier

This setup is optimized for AWS Free Tier:
- **On-demand billing**: Pay only for what you use
- **Free Tier limits**: 25 GB storage, 25 read/write capacity units
- **Cost**: Should be $0 for typical hackathon usage

## Next Steps

After completing these setup steps:
1. Create the Lambda function (backend logic)
2. Set up API Gateway
3. Deploy the frontend
4. Configure IAM roles and permissions

## Requirements Validated

- ✓ Requirement 2.1: DynamoDB table stores schemes with all required fields
- ✓ Requirement 2.3: Category validation (education, farmer, business, healthcare, housing)
- ✓ Requirement 14.1: System only accepts schemes with valid categories
- ✓ Requirement 14.4: DynamoDB schema enforces presence of category field
