# Billing visibility: verified blocker and owner actions

The remediation rechecked project `maadhyam-1610`. Billing is enabled and linked to account `016C3C-CA523C-27545A`. Budget listing as `chaudharishreyas21@gmail.com` still returns **PERMISSION_DENIED**, even with the correct quota project. No billing ownership, IAM binding, budget, alert threshold or spending limit was changed during this remediation.

The reported ₹28K promotional credits remain an owner-provided statement. Available credit balance, expiry, budget thresholds, alert recipients and actual project charges could not be independently verified. This is a billing-account permission limitation, not a failed application deployment.

## Owner-side resolution

1. Open [Google Cloud Billing](https://console.cloud.google.com/billing), select the linked billing account, and confirm that `maadhyam-1610` appears under its linked projects.
2. An existing billing-account administrator can open Account management → Permissions and grant the signed-in reviewer **Billing Account Viewer (`roles/billing.viewer`) on the billing account**. A project Owner role alone does not grant this account-wide visibility. Do not change ownership or grant Billing Account Administrator just to inspect costs.
3. Alternatively, keep account access private and perform the following checks as the owner, recording the results for the submission handoff.
4. In Budgets & alerts, inspect the budget's project scope, amount/currency, actual/forecast threshold percentages, credit-treatment settings and email/Monitoring notification channels. Verify that the intended recipients can receive alerts. Do not assume an alert exists because the API is enabled.
5. In the billing account's Credits/credit details view, check the remaining promotional amount, expiration and applicable scope. In Reports or Cost table, filter to `maadhyam-1610` and the current period; inspect Cloud Run, Vertex AI, Firestore, Firebase Hosting and Artifact Registry, including credit adjustments.
6. If only a custom read-only role is appropriate, budget inspection needs `billing.budgets.list` and `billing.budgets.get`; credit listing needs `billing.credits.list`. The predefined viewer role also supplies relevant billing cost visibility. See Google's [billing role permissions](https://docs.cloud.google.com/iam/docs/roles-permissions/billing) and [Budget API access control](https://docs.cloud.google.com/billing/docs/how-to/budget-api-access-control).

After authorized access is available, repeat:

```powershell
$env:CLOUDSDK_BILLING_QUOTA_PROJECT='maadhyam-1610'
gcloud billing budgets list --billing-account=016C3C-CA523C-27545A --format=json --quiet
```

## Application cost controls already verified

Cloud Run remains on revision `maadhyam-api-00002-grr`, with service and revision minimum instances zero and maximum instances two. Runtime bounds are one CPU, 512 MiB, concurrency four and a 55-second request timeout. Vertex configuration retains one SDK attempt, a 30-second AI timeout, 2,048 output tokens and per-instance authenticated admission limits.

The remediation introduces no backend build, Cloud Run deployment, new service, database, VM, GPU or always-on infrastructure. Frontend Hosting deployment and small fictional acceptance requests are the only application release operations. The existing two registry images are retained for rollback; none was deleted.

**Billing alerts, instance caps and per-instance request limits are not hard currency spending caps.** Credits and rates can change, and Vertex capacity is not reserved. Owner-side verification remains necessary; no verified charge or credit total is claimed here.
