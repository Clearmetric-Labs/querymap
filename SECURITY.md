# Security Policy

`querymap` is a local static-analysis tool. It does not ship authentication,
RBAC, RLS, route handlers, or service-side runtime surfaces as part of this OSS
package.

## Reporting A Vulnerability

Do not file public issues for suspected vulnerabilities.

Use the repository host's private security reporting mechanism if one is
available. If private reporting is not enabled yet, contact the maintainers
through the repository hosting platform and request a private channel before
sharing details.

Include:

- affected version or commit
- impact summary
- reproduction steps
- any proof-of-concept material needed to verify the issue

## Scope

Security reports should focus on vulnerabilities in the OSS package itself.
Requests to add auth, RBAC, RLS, or unrelated platform controls are out of scope
for this repository.
