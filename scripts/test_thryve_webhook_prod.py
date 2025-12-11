#!/usr/bin/env python3
"""
Script to simulate Thryve webhook requests to PRODUCTION with zstandard compression
Usage: python scripts/test_thryve_webhook_prod.py
"""

import zstandard as zstd
import json
import requests
import sys
from datetime import datetime, timezone
from typing import Dict, Any

# Production configuration
PRODUCTION_BASE_URL = "https://api.yourhealth1place.eu"
PRODUCTION_WEBHOOK_URL = f"{PRODUCTION_BASE_URL}/api/v1/webhooks/thryve/data-push"
PRODUCTION_END_USER_ID = "a9bdec856974e93648c6674ac706c9dd"

# Sample webhook payload structure
def create_sample_epoch_payload(end_user_id: str = PRODUCTION_END_USER_ID) -> Dict[str, Any]:
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


def create_sample_daily_payload(end_user_id: str = PRODUCTION_END_USER_ID) -> Dict[str, Any]:
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
        print("⚠️  PRODUCTION ENVIRONMENT - Be careful!")
        
        response = requests.post(
            webhook_url,
            data=compressed_body,
            headers=headers,
            timeout=30,
            verify=True  # Verify SSL certificate
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response Body: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Response Body (text): {response.text}")
        
        return response
        
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Error: {e}")
        print("   Check SSL certificate configuration")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending request: {e}")
        return None


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test Thryve webhook with zstandard compression - PRODUCTION",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Test epoch event (default)
  python scripts/test_thryve_webhook_prod.py
  
  # Test daily event
  python scripts/test_thryve_webhook_prod.py --event-type daily
  
  # Use custom endUserId
  python scripts/test_thryve_webhook_prod.py --end-user-id "your_access_token"
  
  # Use custom payload file
  python scripts/test_thryve_webhook_prod.py --payload path/to/payload.json

Production URL: {PRODUCTION_WEBHOOK_URL}
Default endUserId: {PRODUCTION_END_USER_ID}
        """
    )
    parser.add_argument(
        "--url",
        type=str,
        default=PRODUCTION_WEBHOOK_URL,
        help=f"Webhook URL (default: {PRODUCTION_WEBHOOK_URL})"
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
        default=PRODUCTION_END_USER_ID,
        help=f"Thryve endUserId (access token) to use (default: {PRODUCTION_END_USER_ID})"
    )
    parser.add_argument(
        "--payload",
        type=str,
        help="Path to JSON file containing custom payload (optional)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be sent without actually sending (dry run mode)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Thryve Webhook Tester - PRODUCTION (Zstandard Compression)")
    print("=" * 60)
    print(f"⚠️  WARNING: This will send requests to PRODUCTION!")
    print(f"   URL: {args.url}")
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
    
    # Dry run mode
    if args.dry_run:
        print("\n" + "-" * 60)
        print("🔍 DRY RUN MODE - Request will NOT be sent")
        print(f"   Would send to: {args.url}")
        print(f"   Payload size: {len(compressed_body)} bytes")
        print("   Use without --dry-run to actually send the request")
        return
    
    # Confirm before sending to production
    print("\n" + "-" * 60)
    print("⚠️  PRODUCTION ENVIRONMENT DETECTED")
    response = input("   Are you sure you want to send this to production? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("   Cancelled by user")
        sys.exit(0)
    
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

