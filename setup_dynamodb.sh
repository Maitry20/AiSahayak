#!/bin/bash
# Setup script for DynamoDB table creation and seeding
# Tasks 1.1 and 1.2: Create table and seed with initial data

set -e  # Exit on error

echo "=========================================="
echo "AI-Sahayak DynamoDB Setup"
echo "=========================================="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "✗ AWS CLI is not configured or credentials are invalid"
    echo "  Please run: aws configure"
    exit 1
fi

echo "✓ AWS credentials verified"
echo ""

# Step 1: Create DynamoDB table
echo "Step 1: Creating DynamoDB table..."
echo "=========================================="
python3 create_dynamodb_table.py
if [ $? -ne 0 ]; then
    echo "✗ Failed to create table"
    exit 1
fi
echo ""

# Step 2: Seed with sample schemes
echo "Step 2: Seeding table with sample schemes..."
echo "=========================================="
python3 seed_schemes.py
if [ $? -ne 0 ]; then
    echo "✗ Failed to seed schemes"
    exit 1
fi
echo ""

echo "=========================================="
echo "✓ DynamoDB setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Create Lambda function for backend logic"
echo "  2. Set up API Gateway"
echo "  3. Deploy frontend application"
