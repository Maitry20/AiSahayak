#!/bin/bash

# AI-Sahayak Lambda IAM Role Setup Script
# Task 2.1: Create Lambda execution role
# Requirements: 11.1, 15.6

set -e  # Exit on error

echo "=========================================="
echo "AI-Sahayak Lambda IAM Role Setup"
echo "Task 2.1: Create Lambda execution role"
echo "=========================================="
echo ""

# Check if AWS CLI is configured
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured"
    echo "Please run: aws configure"
    exit 1
fi
echo "✓ AWS credentials verified"
echo ""

# Check if Python is available
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi
echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if boto3 is installed
echo "Checking boto3 installation..."
if ! python3 -c "import boto3" &> /dev/null; then
    echo "⚠ boto3 not found, installing..."
    pip install boto3
fi
echo "✓ boto3 is installed"
echo ""

# Check if policy files exist
echo "Checking policy files..."
if [ ! -f "iam_trust_policy.json" ]; then
    echo "❌ Error: iam_trust_policy.json not found"
    exit 1
fi
if [ ! -f "iam_permissions_policy.json" ]; then
    echo "❌ Error: iam_permissions_policy.json not found"
    exit 1
fi
echo "✓ Policy files found"
echo ""

# Run the Python script to create IAM role
echo "Creating IAM role..."
echo ""
python3 create_iam_role.py

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ IAM Role Setup Complete!"
    echo "=========================================="
    exit 0
else
    echo ""
    echo "=========================================="
    echo "❌ IAM Role Setup Failed"
    echo "=========================================="
    exit 1
fi
