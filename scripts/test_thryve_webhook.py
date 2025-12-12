#!/usr/bin/env python3
"""
Script to simulate Thryve webhook requests with zstandard compression
Usage: python scripts/test_thryve_webhook.py
"""

import zstandard as zstd
import json
import requests
import sys
from datetime import datetime, timezone
from typing import Dict, Any

# Sample webhook payload structure
def create_sample_epoch_payload(end_user_id: str = "8801fc03fa7ff1fe24f61a53efd2a1b3") -> Dict[str, Any]:
    """Create a sample epoch.create event payload"""
    return {
        "endUserId": end_user_id,
        "timestampType": "UTC",
        "type": "event.data.epoch.create",
        "data": [
            {
                "dataSourceId": 8,  # Withings
                "dataSourceName": "Withings",
                "epochData": [
                    {
                        "startTimestamp": int(datetime.now(timezone.utc).timestamp() * 1000) - 3600000,
                        "endTimestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                        "timezoneOffset": 0,
                        "dataTypeId": 1000,  # Example data type ID
                        "value": 75.5
                    },
                    {
                        "startTimestamp": int(datetime.now(timezone.utc).timestamp() * 1000) - 7200000,
                        "endTimestamp": int(datetime.now(timezone.utc).timestamp() * 1000) - 3600000,
                        "timezoneOffset": 0,
                        "dataTypeId": 3000,  # Example data type ID
                        "value": 80.2
                    }
                ]
            }
        ]
    }


def create_sample_daily_payload(end_user_id: str = "8801fc03fa7ff1fe24f61a53efd2a1b3") -> Dict[str, Any]:
    """Create a sample daily.create event payload"""
    today = datetime.now(timezone.utc)
    day_timestamp = int(today.timestamp())
    
    return {
        "endUserId": end_user_id,
        "timestampType": "UTC",
        "type": "event.data.daily.create",
        "data": [
            {
                "dataSourceId": 8,  # Withings
                "dataSourceName": "Withings",
                "dailyData": [
                    {
                        "day": day_timestamp,
                        "timezoneOffset": 0,
                        "dataTypeId": 1000,  # Example data type ID
                        "value": 8500  # Steps example
                    },
                    {
                        "day": day_timestamp,
                        "timezoneOffset": 0,
                        "dataTypeId": 3000,  # Example data type ID
                        "value": 2000  # Calories example
                    }
                ]
            }
        ]
    }


def compress_payload(payload: Dict[str, Any]) -> bytes:
    """Compress JSON payload using zstandard"""
    # Convert to JSON string
    json_str = json.dumps(payload, separators=(',', ':'))
    json_bytes = json_str.encode('utf-8')
    
    # Compress using zstandard
    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(json_bytes)
    
    print(f"Original size: {len(json_bytes)} bytes")
    print(f"Compressed size: {len(compressed)} bytes")
    print(f"Compression ratio: {len(compressed) / len(json_bytes) * 100:.2f}%")
    
    return compressed


def send_webhook_request(compressed_body: bytes, webhook_url: str):
    """Send compressed webhook request to server"""
    try:
        headers = {
            "Content-Type": "application/octet-stream",  # Binary compressed data
        }
        
        print(f"\nSending request to: {webhook_url}")
        response = requests.post(
            webhook_url,
            data=compressed_body,
            headers=headers,
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response Body: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Response Body (text): {response.text}")
        
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Thryve webhook with zstandard compression")
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000/api/v1/webhooks/thryve/data-push",
        help="Webhook URL (default: http://localhost:8000/api/v1/webhooks/thryve/data-push)"
    )
    parser.add_argument(
        "--event-type",
        type=str,
        choices=["epoch", "daily", "daily-update"],
        default="epoch",
        help="Event type to simulate (default: epoch)"
    )
    parser.add_argument(
        "--end-user-id",
        type=str,
        default="8801fc03fa7ff1fe24f61a53efd2a1b3",
        help="Thryve endUserId (access token) to use (default: 8801fc03fa7ff1fe24f61a53efd2a1b3)"
    )
    parser.add_argument(
        "--payload",
        type=str,
        help="Path to JSON file containing custom payload (optional)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Thryve Webhook Tester (Zstandard Compression)")
    print("=" * 60)
    
    # Load payload
    if args.payload:
        print(f"\nLoading custom payload from: {args.payload}")
        try:
            with open(args.payload, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception as e:
            print(f"Error loading payload file: {e}")
            sys.exit(1)
    else:
        print(f"\nCreating sample {args.event_type} payload...")
        if args.event_type == "epoch":
            payload = create_sample_epoch_payload(args.end_user_id)
        elif args.event_type == "daily":
            payload = create_sample_daily_payload(args.end_user_id)
        elif args.event_type == "daily-update":
            payload = create_sample_daily_payload(args.end_user_id)
            payload["type"] = "event.data.daily.update"
    
    print(f"\nPayload structure:")
    print(json.dumps(payload, indent=2))
    
    # Compress payload
    print("\n" + "-" * 60)
    print("Compressing payload...")
    compressed_body = compress_payload(payload)
    
    # Send request
    print("\n" + "-" * 60)
    print("Sending webhook request...")
    response = send_webhook_request(compressed_body, args.url)
    
    if response and response.status_code == 200:
        print("\n✅ Webhook request successful!")
    else:
        print("\n❌ Webhook request failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

