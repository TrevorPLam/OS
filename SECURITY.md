# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please report it to us as described below.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### How to Report

1. Email security concerns to: security@example.com
2. Include the following information:
   - Type of vulnerability
   - Full paths of source file(s) related to the vulnerability
   - The location of the affected code (tag/branch/commit or direct URL)
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the issue, including how an attacker might exploit it

### Response SLA

We will respond to security reports according to the following timeline:

- **Critical (CVSS 9.0+)**: Initial response within 24 hours, fix within 7 days
- **High (CVSS 7.0-8.9)**: Initial response within 48 hours, fix within 30 days
- **Medium/Low**: Tracked in regular maintenance cycles

### What to Expect

- Acknowledgment of your report within the SLA timeframe
- Regular updates on the progress of the fix
- Credit for the discovery (if desired) after the vulnerability is resolved

## Security Best Practices

When working with this repository:

- Never commit secrets, API keys, or credentials
- Use environment variables for sensitive configuration
- Keep dependencies up to date
- Review security advisories for dependencies regularly
- Follow secure coding practices
- For Python backend: Never commit `local_settings.py` or database files

## Security Scanning

This repository uses automated security scanning:

- **Dependency scanning**: Automated checks for vulnerable dependencies (npm and pip)
- **Secret scanning**: Automated detection of accidentally committed secrets
- **SAST**: Static Application Security Testing in CI/CD pipeline

## Security Updates

Security updates will be released as patches to supported versions. Critical security fixes may be backported to older versions on a case-by-case basis.
