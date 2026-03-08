# Quick Start - DynamoDB Setup

## 🚀 Run This Command

```bash
cd backend && ./setup_dynamodb.sh
```

That's it! This will:
1. ✓ Create the DynamoDB table `ai_sahayak_schemes`
2. ✓ Seed it with 5 sample government schemes

## 📋 Prerequisites

```bash
# 1. Configure AWS CLI (one-time setup)
aws configure

# 2. Install Python dependencies
pip install boto3
```

## ✅ Verify Success

```bash
# Check table exists
aws dynamodb describe-table --table-name ai_sahayak_schemes

# View all schemes
aws dynamodb scan --table-name ai_sahayak_schemes
```

## 📚 Need More Details?

- **Full instructions**: See `README.md`
- **Complete guide**: See `SETUP_GUIDE.md`
- **Troubleshooting**: Check the README

## 🎯 What Gets Created

**Table**: `ai_sahayak_schemes`
- Partition Key: `scheme_id` (String)
- Billing: On-demand (Free Tier optimized)

**5 Sample Schemes**:
1. Post Matric Scholarship (education)
2. PM Kisan (farmer)
3. Mudra Loan (business)
4. Ayushman Bharat (healthcare)
5. PM Awas Yojana (housing)

## ⚡ Tasks Completed

- ✅ Task 1.1: Create DynamoDB table with schema
- ✅ Task 1.2: Seed DynamoDB with initial scheme data

## 💰 Cost

**$0** - Optimized for AWS Free Tier
