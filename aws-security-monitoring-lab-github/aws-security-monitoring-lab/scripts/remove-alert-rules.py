#!/usr/bin/env python3
"""Remove only the two named lab rules and their target connections."""

import argparse
import json

import boto3

RULE_NAMES = ("security-lab-sg-changes", "security-lab-trail-changes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default="ap-southeast-1")
    parser.add_argument("--execute", action="store_true", help="Actually remove the lab rules")
    args = parser.parse_args()
    if not args.execute:
        print("Will remove these rules from the default bus in", args.region)
        for name in RULE_NAMES:
            print(" -", name)
        print("Run again with --execute after saving your evidence.")
        return

    events = boto3.client("events", region_name=args.region)
    for name in RULE_NAMES:
        try:
            events.describe_rule(Name=name, EventBusName="default")
        except events.exceptions.ResourceNotFoundException:
            print("Already absent:", name)
            continue
        events.disable_rule(Name=name, EventBusName="default")
        ids = []
        paginator = events.get_paginator("list_targets_by_rule")
        for page in paginator.paginate(Rule=name, EventBusName="default"):
            ids.extend(target["Id"] for target in page["Targets"])
        for offset in range(0, len(ids), 10):
            result = events.remove_targets(
                Rule=name, EventBusName="default", Ids=ids[offset:offset + 10]
            )
            if result["FailedEntryCount"]:
                raise RuntimeError(f"Target removal failed: {json.dumps(result)}")
        events.delete_rule(Name=name, EventBusName="default")
        print("Deleted:", name)
    print("Continue with docs/cleanup.md for SNS, CloudTrail, S3 and the security group.")


if __name__ == "__main__":
    main()
