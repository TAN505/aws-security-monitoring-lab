# Setup and validation

This guide reproduces the single-account lab in `ap-southeast-1`. Run commands in **AWS CloudShell Bash**, from the repository root. Keep all regional resources in the same Region.

The repository scripts consolidate the workflow used for the documented tests. They configure real resources when executed; the packaged versions have not been run against AWS as a separate deployment.

## 1. Prerequisites

- An AWS account with access to CloudTrail, S3, EventBridge, SNS, CloudShell and VPC/EC2 security groups.
- Permission to manage the specific lab resources. Rule setup uses STS identity lookup; EC2 security-group/network-interface reads; SNS topic-policy reads/updates; and EventBridge rule/target writes. Setup and cleanup need the corresponding resource-management permissions as well.
- A usable credit balance or budget for applicable usage. Service availability does not imply unlimited free usage.
- Python 3 and Boto3. The original lab used CloudShell's installed Boto3. If needed, install the dependency with `python3 -m pip install -r requirements.txt`.
- An email address you control for confirming the SNS subscription.

GuardDuty is not required for this adapted design. Check your current account's service eligibility rather than assuming every Free-plan account has identical access.

## 2. Create the private log bucket

In S3, create a **General purpose** bucket in Singapore with a globally unique name. Keep Block all public access enabled, use Bucket owner enforced ownership, and use SSE-S3 encryption. Versioning can remain disabled for this short lab.

Set these values in CloudShell, replacing the bucket name:

```bash
LAB_REGION="ap-southeast-1"
LAB_BUCKET="REPLACE_WITH_YOUR_BUCKET_NAME"
```

Find your account ID locally:

```bash
aws sts get-caller-identity --query Account --output text
```

Open [the bucket-policy template](../policies/cloudtrail-bucket-policy.template.json). Replace every `REPLACE_BUCKET_NAME`, `REPLACE_ACCOUNT_ID` and `REPLACE_REGION` value, then save it through **S3 → bucket → Permissions → Bucket policy**. For an existing bucket, merge the two statements with its existing policy instead of replacing unrelated permissions.

The trail ARN in both conditions must use `ap-southeast-1` and the exact trail name `security-lab-trail`. The `s3:PutObject` resource includes `AWSLogs/<account-id>/*`; no optional log prefix is used here. The policy editor does not expand shell variables. [AWS policy documentation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html)

## 3. Create an active single-Region trail

First inspect existing trails. If an existing trail already captures management events in this Region, assess whether it can be reused to avoid duplicate log delivery. Do not alter or later delete a shared trail for this exercise.

For a dedicated lab trail, run each command separately and check for errors:

```bash
aws cloudtrail create-trail \
  --name security-lab-trail \
  --s3-bucket-name "$LAB_BUCKET" \
  --no-is-multi-region-trail \
  --no-include-global-service-events \
  --enable-log-file-validation \
  --region "$LAB_REGION"
```

```bash
aws cloudtrail put-event-selectors \
  --trail-name security-lab-trail \
  --event-selectors '[{"ReadWriteType":"All","IncludeManagementEvents":true,"DataResources":[]}]' \
  --region "$LAB_REGION"
```

```bash
aws cloudtrail start-logging \
  --name security-lab-trail \
  --region "$LAB_REGION"
```

```bash
aws cloudtrail get-trail-status \
  --name security-lab-trail \
  --region "$LAB_REGION" \
  --no-cli-pager
```

Confirm `IsLogging` is `true`. After delivery, inspect the bucket's Objects tab under:

```text
AWSLogs/<account-id>/CloudTrail/ap-southeast-1/<year>/<month>/<day>/
```

The `.json.gz` objects create the visible folder prefixes automatically. Check `LatestDeliveryError` if logs do not arrive. Creating a trail and starting logging are separate operations. [AWS trail CLI guide](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-and-update-a-trail-by-using-the-aws-cli-create-trail.html)

## 4. Create and confirm SNS email delivery

In SNS, create a **Standard** topic named `security-lab-alerts`. Leave optional features off for this lab. Add an **Email** subscription, open the confirmation email, and confirm it.

Publish a manual test message from the topic page. Continue only after it reaches your inbox. The alert setup script expects this topic to exist in the same account and Region.

## 5. Create an isolated security group

In **VPC → Security groups**, create `security-lab-sg` in an existing VPC. Start with no inbound rules and record its group ID. Keep the group unattached to workloads throughout the exercise.

If no VPC is available, use **Create VPC → VPC only**, name it `security-lab-vpc`, and use a private CIDR such as `10.77.0.0/16`. No subnet, instance, NAT gateway, or VPC endpoint is required for this exercise.

## 6. Configure both detection rules

From the repository root, run:

```bash
python3 scripts/create-alert-rules.py \
  --security-group-id sg-REPLACE_WITH_YOUR_LAB_GROUP \
  --region ap-southeast-1
```

The script validates the group name and checks that no network interface uses it. It merges a dedicated EventBridge publishing statement into the existing SNS topic policy, then creates/updates both named rules and their SNS targets. Re-running it updates those resources rather than creating new names. Unrelated SNS policy statements are preserved.

There is no new custom event bus. The script uses the existing `default` bus and the target's resource policy. [AWS EventBridge permissions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html)

The two pattern files are templates: the security-group ID is inserted by the script. Do not submit its placeholder unchanged.

Check the target for each rule. For example:

```bash
aws events list-targets-by-rule \
  --rule security-lab-sg-changes \
  --event-bus-name default \
  --region ap-southeast-1 \
  --no-cli-pager
```

The target ARN should end in `:security-lab-alerts`. Allow a short propagation interval before generating test actions.

## 7. Test detection and manual containment

1. Open the unattached `security-lab-sg` group.
2. Add an inbound rule: SSH, TCP port 22, source `0.0.0.0/0`.
3. Use description `LAB ONLY - simulated risky change` and save.
4. Check the SNS email for `detail.eventName = AuthorizeSecurityGroupIngress` and the correct group ID.
5. In CloudTrail Event history, inspect the actor, time, source, request parameters, and response/error fields.
6. Remove that SSH rule and save.
7. Verify an empty inbound-rule list and a `RevokeSecurityGroupIngress` email/event.

Public SSH is the controlled test input. An unattached group changes no running workload's network access. The detector alerts on the two configured API actions, so it also matches benign additions/removals.

## 8. Test trail configuration monitoring

On the dedicated lab trail, run:

```bash
aws cloudtrail update-trail \
  --name security-lab-trail \
  --enable-log-file-validation \
  --region ap-southeast-1 \
  --no-cli-pager
```

This requests an `UpdateTrail` operation while retaining validation. Look for its email and CloudTrail event. Then repeat `get-trail-status` and confirm logging remains enabled. Do not disable auditing merely to test the other event names in the pattern.

## 9. Correlate the records

Use the email's **`detail.eventID`** to search CloudTrail Event history. The top-level EventBridge `id` is a different identifier. Set the correct Region and a time range covering the action. JSON timestamps ending in `Z` use UTC; Malaysia time is UTC+08:00.

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventId,AttributeValue=REPLACE_CLOUDTRAIL_EVENT_ID \
  --region ap-southeast-1 \
  --no-cli-pager
```

Both the console and this command depend on Event history availability; the command is not a way to bypass a delivery/indexing delay.

Save evidence locally, write the incident timeline, and follow [cleanup](cleanup.md).
