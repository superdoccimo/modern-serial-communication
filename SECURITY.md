# Security Policy

## Supported Versions

We actively support the following versions of Modern Serial Communication:

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in Modern Serial Communication, please follow these steps:

### 1. Do NOT create a public issue

Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.

### 2. Report privately

Send a detailed report to: **github@minokamo.xyz**

Include the following information:
- Type of vulnerability
- Full paths of source files related to the manifestation of the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

### 3. What to expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours.
- **Assessment**: We will assess the vulnerability and determine its impact within 5 business days.
- **Updates**: We will keep you informed of our progress throughout the process.
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days.

### 4. Responsible Disclosure

- We will work with you to understand and resolve the issue before any public disclosure.
- We will credit you appropriately for the discovery (unless you prefer to remain anonymous).
- We request that you do not publicly disclose the vulnerability until we have had a chance to address it.

## Security Best Practices

When using Modern Serial Communication:

### Serial Port Access
- **Principle of Least Privilege**: Run with minimum required permissions
- **User Groups**: On Linux, add users to `dialout` group instead of using `sudo`
- **Port Validation**: The software validates port access before connection

### Network Features
- **Local Use**: Network features are designed for local/trusted network use
- **Firewall**: Configure firewall rules when using network bridging features
- **Authentication**: Network features do not include authentication - use in trusted environments only

### File Operations
- **Configuration Files**: Stored in user directory, not system-wide
- **Log Files**: Check log file permissions in multi-user environments
- **CSV Exports**: Be mindful of sensitive data in exported files

### Dependencies
- **Regular Updates**: Keep dependencies updated using `pip install -U -r requirements.txt`
- **Virtual Environments**: Use virtual environments to isolate dependencies
- **Security Scanning**: Run `pip-audit` or similar tools to check for known vulnerabilities

## Security Features

### Input Validation
- Port names and paths are validated before use
- Configuration file parsing includes error handling
- User input is sanitized before processing

### Error Handling
- Detailed error messages are logged but not exposed to potential attackers
- Graceful degradation when components fail
- Safe defaults for all configuration options

### Platform Security
- **Linux**: Proper permission checking for serial devices
- **Windows**: Uses standard Windows security model
- **Cross-platform**: No platform-specific security shortcuts

## Known Security Considerations

### Serial Port Access
- Serial port access inherently requires elevated permissions on some systems
- Physical access to serial ports can be used for privilege escalation
- Some virtual serial ports may bypass normal permission checks

### Network Bridge Mode
- TCP bridging features do not include encryption
- Network traffic is sent in plaintext
- Designed for local/lab use, not production deployment

### Configuration Files
- Configuration files may contain sensitive settings
- File permissions should be set appropriately by users
- No built-in encryption for configuration data

## Security Updates

Security updates will be:
- Released as soon as possible after verification
- Documented in the changelog with severity levels
- Announced through GitHub security advisories
- Backported to supported versions when applicable

## Contact

For security-related questions or concerns:
- Email: github@minokamo.xyz
- Subject: "[SECURITY] Modern Serial Communication - [Brief Description]"

For general questions about security features:
- Create a GitHub discussion
- Use the "Security" category

Thank you for helping keep Modern Serial Communication secure!