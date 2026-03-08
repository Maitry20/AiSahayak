#!/usr/bin/env python3
"""
Script to seed DynamoDB table with initial scheme data
Task 1.2: Seed DynamoDB with initial scheme data
Requirements: 2.1, 2.3, 14.1
"""

import boto3
import sys

# Sample schemes from design.md
SCHEMES = [
    {
        "scheme_id": "SCH001",
        "scheme_name": "Post Matric Scholarship",
        "category": "education",
        "description": "Scholarship for students from economically weaker sections",
        "eligibility": "Family income below 2.5 lakh",
        "benefits": "Covers tuition fees and maintenance allowance"
    },
    {
        "scheme_id": "SCH002",
        "scheme_name": "PM Kisan",
        "category": "farmer",
        "description": "Income support for farmers",
        "eligibility": "All landholding farmers",
        "benefits": "Rs 6000 per year in three installments"
    },
    {
        "scheme_id": "SCH003",
        "scheme_name": "Mudra Loan",
        "category": "business",
        "description": "Loans for micro and small enterprises",
        "eligibility": "Non-corporate, non-farm small/micro enterprises",
        "benefits": "Loans up to Rs 10 lakh"
    },
    {
        "scheme_id": "SCH004",
        "scheme_name": "Ayushman Bharat",
        "category": "healthcare",
        "description": "Health insurance for economically vulnerable families",
        "eligibility": "Families identified through SECC database",
        "benefits": "Health cover of Rs 5 lakh per family per year"
    },
    {
        "scheme_id": "SCH005",
        "scheme_name": "PM Awas Yojana",
        "category": "housing",
        "description": "Affordable housing for urban poor",
        "eligibility": "EWS/LIG families without pucca house",
        "benefits": "Financial assistance for house construction"
    }
]

VALID_CATEGORIES = {"education", "farmer", "business", "healthcare", "housing"}

def validate_scheme(scheme):
    """
    Validate scheme has all required fields and valid category
    Requirements: 2.1, 2.3, 14.1
    """
    required_fields = ["scheme_id", "scheme_name", "category", "description", "eligibility", "benefits"]
    
    # Check all required fields are present
    for field in required_fields:
        if field not in scheme or not scheme[field]:
            raise ValueError(f"Scheme missing required field: {field}")
    
    # Validate category
    if scheme["category"] not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category '{scheme['category']}'. Must be one of: {VALID_CATEGORIES}")
    
    return True

def seed_schemes():
    """
    Insert 5 sample schemes into DynamoDB table
    Validates all schemes have required fields and valid categories
    """
    try:
        dynamodb = boto3.client('dynamodb')
        table_name = 'ai_sahayak_schemes'
        
        print(f"Seeding DynamoDB table '{table_name}' with {len(SCHEMES)} schemes...")
        print()
        
        success_count = 0
        
        for scheme in SCHEMES:
            try:
                # Validate scheme before inserting
                validate_scheme(scheme)
                
                # Convert to DynamoDB format
                item = {
                    'scheme_id': {'S': scheme['scheme_id']},
                    'scheme_name': {'S': scheme['scheme_name']},
                    'category': {'S': scheme['category']},
                    'description': {'S': scheme['description']},
                    'eligibility': {'S': scheme['eligibility']},
                    'benefits': {'S': scheme['benefits']}
                }
                
                # Insert into DynamoDB
                dynamodb.put_item(
                    TableName=table_name,
                    Item=item
                )
                
                print(f"✓ Inserted: {scheme['scheme_name']} ({scheme['category']})")
                success_count += 1
                
            except Exception as e:
                print(f"✗ Failed to insert {scheme.get('scheme_name', 'Unknown')}: {str(e)}")
        
        print()
        print(f"✓ Successfully seeded {success_count}/{len(SCHEMES)} schemes!")
        
        # Verify by scanning the table
        print("\nVerifying inserted schemes...")
        response = dynamodb.scan(TableName=table_name)
        items = response.get('Items', [])
        print(f"✓ Table now contains {len(items)} schemes")
        
        return success_count == len(SCHEMES)
        
    except Exception as e:
        print(f"✗ Error seeding schemes: {str(e)}")
        return False

if __name__ == "__main__":
    success = seed_schemes()
    sys.exit(0 if success else 1)
