# Security policy

Please report vulnerabilities privately through GitHub: **[Report a vulnerability](https://github.com/graviton94/pickaxetax/security/advisories/new)**. Don't use public issues for this.

In scope (high priority):
- any way for the web app to send conversation text off the device (it is designed to be impossible: CSP `connect-src` is limited to the contribution worker, which only accepts allowlisted numbers);
- any way to smuggle free text or personal data through the contribution validators (`site/contrib.js`, `pickaxetax/contrib.py`);
- the local proxy leaking prompts, responses or API keys to disk or logs;
- the guard hook blocking legitimate work in a way the "repeat to allow" rule doesn't recover;
- abuse of the contribution worker (bypassing proof of work, rate limits or deletion tokens).

We aim to acknowledge reports within 72 hours and to publish a fix and an advisory once it is resolved.
