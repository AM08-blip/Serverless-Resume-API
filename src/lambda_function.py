
import json
import os
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get("TABLE_NAME", "ResumeData")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def load_json_data():
    file_path = os.path.join(
        os.path.dirname(__file__),
        "resume.json"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def seed_database():
    resume = load_json_data()

    records = [
        {
            "PK": "PERSONAL",
            "SK": "PROFILE",
            **resume["personal"]
        }
    ]

    for i, item in enumerate(resume["experience"], 1):
        records.append({
            "PK": "EXPERIENCE",
            "SK": f"EXP#{i:03d}",
            **item
        })

    for i, item in enumerate(resume["education"], 1):
        records.append({
            "PK": "EDUCATION",
            "SK": f"EDU#{i:03d}",
            **item
        })

    for i, skill in enumerate(resume["skills"], 1):
        records.append({
            "PK": "SKILLS",
            "SK": f"SKILL#{i:03d}",
            "skill": skill
        })

    with table.batch_writer() as batch:
        for record in records:
            batch.put_item(Item=record)


def decimal_to_float(data):
    if isinstance(data, list):
        return [decimal_to_float(item) for item in data]

    if isinstance(data, dict):
        return {
            key: decimal_to_float(value)
            for key, value in data.items()
        }

    if isinstance(data, Decimal):
        return float(data)

    return data


def lambda_handler(event, context):

    path = event.get("path", "/")
    section = path.strip("/").lower()

    allowed_sections = [
        "personal",
        "experience",
        "education",
        "skills"
    ]

    if section not in allowed_sections:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "message": "Endpoint not found"
            })
        }

    try:
        response = table.query(
            KeyConditionExpression=Key("PK").eq(section.upper())
        )

        items = response.get("Items", [])

        # Initialize DynamoDB from JSON if this section is empty
        if not items:
            seed_database()

            response = table.query(
                KeyConditionExpression=Key("PK").eq(section.upper())
            )

            items = response.get("Items", [])

        if not items:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "message": "Resume data not found"
                })
            }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(decimal_to_float(items))
        }

    except Exception as error:
        print("Error:", str(error))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal server error"
            })
        }