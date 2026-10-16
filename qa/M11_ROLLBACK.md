# M11 rollback

No rollback was performed. Preserve Firestore records, Firebase anonymous users and browser-local Vault data throughout rollback.

## Backend traffic rollback

The previous revision `maadhyam-api-00001-f64` passed hosted acceptance. The current revision is `maadhyam-api-00002-grr`. To return traffic to the previous tested revision:

```powershell
gcloud run services update-traffic maadhyam-api --project=maadhyam-1610 --region=asia-south1 --to-revisions=maadhyam-api-00001-f64=100
```

Verify both health routes, authenticated list/resume and application ownership. Recheck that service minimum instances is zero and maximum is two. The older revision already has revision minimum zero and maximum two. Do not delete either revision or databases. Returning to revision 00001 restores its generic provider failure responses; current revision 00002 has improved quota/IAM/model/timeout handling.

To restore the current verified revision later, use the same command with `maadhyam-api-00002-grr=100`. For future releases, capture the actual stable revision before deployment rather than assuming these names remain appropriate.

## Firebase Hosting rollback

The pre-deployment release list was empty: this was the site's first Hosting deployment. There is no earlier live Hosting release to restore. Current stable version is `sites/maadhyam-1610/versions/e354c084966d0cdd`, release `sites/maadhyam-1610/releases/1792172321125000`.

After a future Hosting deployment, use Firebase Console → Hosting → release history → Roll back on this verified release. Alternatively create a new Hosting REST release using the retained version, following the [official release API](https://firebase.google.com/docs/reference/hosting/rest/v1beta1/sites.releases/create). Do not delete the site or disable unrelated Firebase services. Hosting has no `pinTag`, so its rollback does not select a backend revision automatically.

## Source rollback

M11 implementation checkpoint: `2c1672536318abf03f4930608c377b3d39cb1709`. Provider failure correction: `06c59cb1c94437907af7075f86dd6bc86c0d4242`. Original checkout: `f2a0e4e`.

For source rollback, first review the working tree and preserve unrelated local work. Use reviewed `git revert` commits on `release/m10-m12-recovery`; revert dependent commits in reverse order. Never use hard reset, clean, force push or a destructive branch switch. A source revert does not alter the deployed image or restore Hosting by itself; build, test and deploy a deliberate rollback release only if needed.

No schema migration was introduced. Existing application IDs, UID-scoped paths and optimistic revisions remain intact. Do not reset Firestore, delete anonymous users, upload Vault bytes or clear browser storage as part of rollback.
