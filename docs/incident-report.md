# Incident exercise report: public SSH rule change

**Classification:** Controlled configuration-change exercise  
**Date:** 15 October 2026  
**Region:** Asia Pacific (Singapore), `ap-southeast-1`  
**Resource:** An unattached lab security group  
**Operator identity shown in evidence:** `Lab2`

## Summary

I added an inbound rule allowing TCP port 22 from `0.0.0.0/0` to the lab security group. CloudTrail recorded the API action, EventBridge matched it, and SNS delivered an email. I inspected the event, removed the rule, and received a second alert. The revocation record reported success.

This was a known lab action. There was no running workload attached to the group and no evidence of an actual compromise in this exercise. The goal was to practise identifying, investigating, and reversing a risky configuration.

## Timeline

Times below are API-event timestamps, not measured email-delivery times.

| UTC | Malaysia time (UTC+08:00) | Action | Evidence |
| --- | --- | --- | --- |
| 08:19:40 | 16:19:40 | Added inbound SSH permission | `AuthorizeSecurityGroupIngress`; SNS email and CloudTrail record |
| 08:26:35 | 16:26:35 | Removed inbound SSH permission | `RevokeSecurityGroupIngress`; SNS email; successful API response |
| 08:39:49 | 16:39:49 | Requested a trail update retaining log-file validation | `UpdateTrail`; SNS email and CloudTrail record |

The interval between addition and removal was **6 minutes 55 seconds**. This is the duration between the two lab actions, not a measured detection latency or a production response-time metric.

## Investigation

The authorization request showed:

| Field | Observed value or interpretation |
| --- | --- |
| `eventName` | `AuthorizeSecurityGroupIngress` |
| `eventSource` | `ec2.amazonaws.com` |
| `awsRegion` | `ap-southeast-1` |
| `userIdentity` | The lab operator's IAM user |
| `requestParameters.groupId` | The lab security group |
| `ipProtocol` | `tcp` |
| `fromPort` / `toPort` | `22` / `22` |
| `cidrIp` | `0.0.0.0/0` |
| Description | `LAB ONLY - simulated risky change` |

The source permits any IPv4 address. If attached to a reachable SSH workload, this permission could expand its exposure. Actual reachability would also depend on the workload, network routing, and other controls; the permission alone does not prove an exposed server.

## Containment and verification

I deleted the inbound SSH rule and saved the security-group configuration. The resulting notification contained `RevokeSecurityGroupIngress`, `_return: true`, and the revoked TCP/22 rule with source `0.0.0.0/0`.

The [revocation Event history capture](../screenshots/06-ingress-revoked.png) corroborates the action and its timestamp. The successful response establishes that AWS accepted the revocation. An independent final screenshot of the empty inbound-rule list is not included in this package.

## Additional detection test

I called `UpdateTrail` with `enableLogFileValidation` set to `true`. The event was found in CloudTrail and the alert email arrived. This confirmed the second rule's `UpdateTrail` path. The other configured CloudTrail action names were not exercised as attack simulations.

## Evidence references

| Action | CloudTrail event ID | Screenshot |
| --- | --- | --- |
| Inbound rule added | `ed7eec85-f3db-4ff2-803e-cde6d2d120ae` | [Authorization](../screenshots/05-ingress-added.png) |
| Inbound rule removed | `48eb74ec-4dbd-4308-8d12-d9bf5487e39e` | [Revocation](../screenshots/06-ingress-revoked.png) |
| Trail updated | `65c592d0-ef9a-49b5-b55d-52eeb1cbd5c4` | [Trail update](../screenshots/07-trail-updated.png) |

These are correlation identifiers, not credentials. Account IDs, access-key IDs, and source IP addresses are omitted from the written report. Raw notification JSON is not published.

## Outcome and follow-up

- Validated email delivery for all three tested actions.
- Practised correlation using the CloudTrail event ID and request/response fields.
- Completed the simulated containment action through rule revocation.
- Identified opportunities to extend event coverage and monitor alert-delivery failures.
- Prepared cleanup instructions; infrastructure teardown is not independently evidenced in this report.
