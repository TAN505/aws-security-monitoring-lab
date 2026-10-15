# Cleanup runbook

Perform these steps after exporting evidence. This is a runbook, not a claim that the documented environment has already been deleted. Keep any shared or pre-existing resources that were reused.

## 1. Remove the detection rules

Preview the two rule names:

```bash
python3 scripts/remove-alert-rules.py --region ap-southeast-1
```

Delete them and their target connections:

```bash
python3 scripts/remove-alert-rules.py --region ap-southeast-1 --execute
```

Targets must be removed before rules can be deleted. The script checks target-removal failures and stops on an error. It does not delete the default event bus. [AWS rule deletion documentation](https://docs.aws.amazon.com/cli/latest/reference/events/delete-rule.html)

## 2. Delete the lab security group

In **VPC → Security groups**, verify the name and ID of `security-lab-sg`, then delete it. Remove only the VPC created specifically for this lab, if one was created; preserve any shared/default VPC.

## 3. Stop and delete the dedicated trail

For the trail created specifically for this lab, run separately:

```bash
aws cloudtrail stop-logging \
  --name security-lab-trail \
  --region ap-southeast-1
```

```bash
aws cloudtrail delete-trail \
  --name security-lab-trail \
  --region ap-southeast-1
```

Deleting the trail leaves its existing S3 files in place. [AWS trail deletion documentation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-delete-trails-console.html)

## 4. Remove the dedicated S3 log bucket

After saving any logs needed for the report, select the dedicated lab bucket in S3, choose **Empty**, and then delete the bucket. If versioning was enabled, remove all versions and delete markers as part of emptying it. This permanently removes the stored log files.

## 5. Remove SNS

Delete the lab email subscription and the dedicated `security-lab-alerts` topic in Singapore. Deleting the topic also removes its resource policy.

If you keep the topic for another purpose, remove only the statement with SID `SecurityLabAllowEventBridgePublish` after confirming no remaining lab rule needs it. Preserve unrelated statements. The supplied scripts do not create an IAM execution role.

## 6. Verify

- The two lab rules are absent.
- The lab security group is absent.
- The dedicated trail is absent.
- The dedicated S3 bucket is absent, or intentionally retained with its storage cost understood.
- The lab SNS topic/subscription is absent.
- Billing/Free Tier usage has been reviewed after reporting updates.

CloudTrail Event history can still show previous management events after the dedicated trail is deleted. That does not mean the trail is still delivering files.
