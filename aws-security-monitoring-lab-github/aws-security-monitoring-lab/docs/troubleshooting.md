# Troubleshooting notes

## CloudTrail cannot use the S3 bucket

**Observed error:** `InsufficientS3BucketPolicyException` during `CreateTrail`.

The policy's trail ARN had an incorrectly written Region. Correcting it to `ap-southeast-1` resolved the issue.

Check the bucket name, account ID, exact trail name, and Region in both policy statements. The bucket needs `s3:GetBucketAcl`; the destination object path needs `s3:PutObject`. The bucket name passed to `--s3-bucket-name` is a name, not an ARN. Keep Block Public Access enabled.

## S3 initially has no folders

CloudTrail creates the object prefixes when logs arrive. There is no need to create `AWSLogs` manually.

```bash
aws cloudtrail get-trail-status \
  --name security-lab-trail \
  --region ap-southeast-1 \
  --no-cli-pager
```

Check `IsLogging`, `LatestDeliveryTime`, and any `LatestDeliveryError`. A missing trail means creation did not succeed in the current account/Region. A logging trail can still have delivery errors.

## Rules are difficult to locate in the console

During the lab, the console indicated that rules had moved to the owning event bus. The lab used CloudShell instead of relying on a particular console layout.

Use the supplied script on the **existing default event bus**. Creating a new custom event bus does not automatically route the AWS service events to it. CloudShell uses the current AWS identity and does not bypass account-plan or IAM restrictions.

## Email arrives, but Event history does not show the record yet

Check Singapore Region, clear the previous attribute filter, and use a time range containing the event. Search by the email's `detail.eventID`, not its top-level `id`. Allow time for Event history to update.

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventId,AttributeValue=REPLACE_CLOUDTRAIL_EVENT_ID \
  --region ap-southeast-1 \
  --no-cli-pager
```

If this returns an empty array, check the ID, Region, account, and timestamp before assuming delivery failed. Preserve the original email locally for comparison.

## Event exists but the email does not arrive

1. Publish a manual test message to SNS; verify the subscription is confirmed and check spam folders.
2. Inspect the relevant rule with `aws events describe-rule` and its target with `aws events list-targets-by-rule`.
3. Confirm the rule uses the `default` bus and the security-group pattern contains the correct ID.
4. Check the SNS topic policy grants `events.amazonaws.com` permission to publish to this exact topic, or check the execution role if you chose that approach.
5. Inspect EventBridge rule monitoring for matches and failed invocations.
6. Generate a new test action after the rule is active. Rules do not automatically replay previous Event history records.

## Template values are still present

`REPLACE_...` markers are intentional placeholders. Set real values locally before applying a policy or command. Bash variable names are case-sensitive: `$LAB_BUCKET` and `$lab_bucket` are different. The S3 policy editor does not evaluate Bash variables.

## An alert does not mean the API action succeeded

The patterns match request event names. Inspect `errorCode`, `errorMessage`, response data, and current resource state. An authorized change or a rejected request may also match a rule.

## References

- [CloudTrail bucket permissions](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html)
- [CloudTrail trail status](https://docs.aws.amazon.com/cli/latest/reference/cloudtrail/get-trail-status.html)
- [CloudTrail events in EventBridge](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-service-event-cloudtrail.html)
- [EventBridge target permissions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html)
