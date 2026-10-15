#!/usr/bin/env python3
"""Configure the two lab EventBridge rules and an existing SNS topic's policy."""

import argparse
import json
import re
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
POLICY_SID = "SecurityLabAllowEventBridgePublish"
TARGET_ID = "SecurityLabEmail"


def load_pattern(filename):
    return json.loads((ROOT / "patterns" / filename).read_text(encoding="utf-8"))


def merge_publish_permission(policy, topic_arn):
    """Replace only this lab's statement; retain all unrelated permissions."""
    statements = policy.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    policy.setdefault("Version", "2012-10-17")
    policy["Statement"] = [s for s in statements if s.get("Sid") != POLICY_SID]
    policy["Statement"].append({
        "Sid": POLICY_SID,
        "Effect": "Allow",
        "Principal": {"Service": "events.amazonaws.com"},
        "Action": "sns:Publish",
        "Resource": topic_arn,
    })
    return policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default="ap-southeast-1")
    parser.add_argument("--security-group-id", required=True)
    parser.add_argument("--topic-name", default="security-lab-alerts")
    args = parser.parse_args()
    if not re.fullmatch(r"sg-(?:[0-9a-f]{8}|[0-9a-f]{17})", args.security_group_id):
        parser.error("Provide a real security-group ID, not the example placeholder.")

    session = boto3.Session(region_name=args.region)
    identity = session.client("sts").get_caller_identity()
    partition = identity["Arn"].split(":")[1]
    topic_arn = (
        f"arn:{partition}:sns:{args.region}:{identity['Account']}:{args.topic_name}"
    )
    ec2 = session.client("ec2")
    group = ec2.describe_security_groups(GroupIds=[args.security_group_id])["SecurityGroups"][0]
    if group["GroupName"] != "security-lab-sg":
        parser.error("Use the security group named security-lab-sg for this exercise.")
    attached = ec2.describe_network_interfaces(
        Filters=[{"Name": "group-id", "Values": [args.security_group_id]}],
        MaxResults=5,
    )["NetworkInterfaces"]
    if attached:
        parser.error("The lab security group must be unattached to network interfaces.")

    sns = session.client("sns")
    events = session.client("events")
    attributes = sns.get_topic_attributes(TopicArn=topic_arn)["Attributes"]
    policy = json.loads(attributes.get("Policy", '{"Version":"2012-10-17","Statement":[]}'))
    policy = merge_publish_permission(policy, topic_arn)
    sns.set_topic_attributes(
        TopicArn=topic_arn, AttributeName="Policy", AttributeValue=json.dumps(policy)
    )

    sg_pattern = load_pattern("security-group-changes.json")
    sg_pattern["detail"]["requestParameters"]["groupId"] = [args.security_group_id]
    rules = [
        ("security-lab-sg-changes", sg_pattern),
        ("security-lab-trail-changes", load_pattern("cloudtrail-changes.json")),
    ]
    for name, pattern in rules:
        response = events.put_rule(
            Name=name,
            EventBusName="default",
            Description="AWS security monitoring lab: configuration-change alerts",
            EventPattern=json.dumps(pattern),
            State="ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS",
        )
        result = events.put_targets(
            Rule=name, EventBusName="default",
            Targets=[{"Id": TARGET_ID, "Arn": topic_arn}],
        )
        if result["FailedEntryCount"]:
            raise RuntimeError(f"Target setup failed for {name}: {json.dumps(result)}")
        print("Configured:", response["RuleArn"])

    print("SNS topic:", topic_arn)
    print("Setup complete. Confirm the email subscription before testing.")


if __name__ == "__main__":
    main()
