# Evidence notes

The screenshots document the operator's AWS lab run on 15 October 2026. File names and captions describe what is actually visible.

| File | Source and handling | What it supports |
| --- | --- | --- |
| `01-cloudtrail-configuration.png` | Account number obscured using an AI image-editing tool; dimensions/rendering may differ from the original | Trail name and Singapore home Region; does not show logging status |
| `02-s3-log-delivery.png` | Account-number prefixes obscured using an AI image-editing tool | CloudTrail log objects in S3 |
| `03-sns-dashboard.png` | Original screenshot copied without modification | One SNS topic and one subscription; not subscription confirmation state |
| `04-notification-inbox.png` | Account numbers obscured using an AI image-editing tool; dimensions/rendering may differ from the original | Notification messages received; collapsed previews do not show complete event payloads |
| `05-ingress-added.png` | Original Event history screenshot copied without modification | Authorization event, actor label, time, and correlation ID |
| `06-ingress-revoked.png` | Original Event history screenshot copied without modification | Revocation event, actor label, time, and correlation ID |
| `07-trail-updated.png` | Original Event history screenshot copied without modification | Trail update event, actor label, time, and correlation ID |

The account number, source IP addresses, and access-key identifiers are excluded from the published text. Detailed request screenshots containing IP addresses and raw email JSON were not added to this repository. The Event history screenshots retain non-secret resource/event identifiers and the lab username for correlation.

The written report also uses details supplied in the original lab records, including TCP port 22, source `0.0.0.0/0`, the successful revocation response, and `enableLogFileValidation: true`. It does not present reconstructed JSON as an original export.

Evidence not included: an independent screenshot of the final empty inbound-rule list, a final trail-status result following the update, and teardown verification. The setup/runbook explains how to collect those checks; the report does not claim they were independently captured.
