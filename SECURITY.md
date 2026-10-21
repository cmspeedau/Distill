# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Use GitHub's private reporting: go to the **Security** tab of this repository and choose **Report a vulnerability**.

Include what you found, steps to reproduce, and the potential impact. You can expect an initial response within a few days.

## Scope

Particularly interesting areas:

- SSRF bypasses (private, loopback, link-local, or cloud metadata addresses, including via redirects or DNS tricks)
- robots.txt handling
- Authentication and API key handling
- Storage path traversal
- Credential storage for databases and S3

## Supported versions

Distill is in early development. Only the latest `main` is supported.
