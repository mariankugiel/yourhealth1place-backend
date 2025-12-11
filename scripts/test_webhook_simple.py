#!/usr/bin/env python3
"""
Simple script to test Thryve webhook with zstandard compression
Quick usage example
"""

import zstandard as zstd
import json
import requests

# Sample payload
payload = {
    "endUserId": "test_access_token_123",
    "timestampType": "UTC",
    "type": "event.data.daily.create",
    "data": [
        {
            "dataSourceId": 8,
            "dataSourceName": "Withings",
            "dailyData": [
                {
                    "day": 1704067200,  # Unix timestamp
                    "timezoneOffset": 0,
                    "dataTypeId": 1,
                    "value": 8500
                }
            ]
        }
    ]
}

# Compress
json_str = json.dumps(payload)
json_bytes = json_str.encode('utf-8')
cctx = zstd.ZstdCompressor()
compressed = cctx.compress(json_bytes)

# Send
url = "http://localhost:8000/api/v1/webhooks/thryve/data-push"
response = requests.post(url, data=compressed, headers={"Content-Type": "application/octet-stream"})

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

