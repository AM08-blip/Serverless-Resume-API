
import json
import os
import boto3
from decimal import Decimal

TABLE_NAME = os.environ.get("TABLE_NAME", "ResumeData")

# Connect to DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

# Read resume JSON file
file_path = os.path.join(
    os.path.dirname(__file__),
    "resume.json"
)

with open(file_path, "r", encoding="utf-8") as file:
    resume = json.load(file, parse_float=Decimal)

# Prepare DynamoDB records
records = []

# Personal information
records.append({
    "PK": "PERSONAL",
    "SK": "PROFILE",
    **resume["personal"]
})

# Work experience
for i, item in enumerate(resume["experience"], 1):
    records.append({
        "PK": "EXPERIENCE",
        "SK": f"EXP#{i:03d}",
        **item
    })

# Education
for i, item in enumerate(resume["education"], 1):
    records.append({
        "PK": "EDUCATION",
        "SK": f"EDU#{i:03d}",
        **item
    })

# Skills
for i, skill in enumerate(resume["skills"], 1):
    records.append({
        "PK": "SKILLS",
        "SK": f"SKILL#{i:03d}",
        "skill": skill
    })

# Upload records
with table.batch_writer() as batch:
    for record in records:
        batch.put_item(Item=record)

print(f"Successfully uploaded {len(records)} resume records!")