# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within SampleSplit, please follow these steps:

### For GitHub Security Advisories (Recommended)

1. Go to the repository's **Security** tab
2. Click **"Report a vulnerability"**
3. Fill out the vulnerability report form
4. Submit with as much detail as possible

### For Email Reporting

If you prefer private disclosure:

1. Do **NOT** create a public GitHub issue
2. Email the maintainer directly with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Timeline**: Varies based on severity
  - Critical: 24-72 hours
  - High: 1-2 weeks
  - Medium: 2-4 weeks
  - Low: Next release
- **Disclosure**: Credit given to reporter (unless anonymous)

---

## Security Features

### Implemented

| Feature | Status | Description |
|---------|--------|-------------|
| Password Hashing | ✅ | Werkzeug's PBKDF2 with SHA256 |
| CSRF Protection | ✅ | Flask-WTF tokens on all forms |
| Rate Limiting | ✅ | Flask-Limiter on auth routes |
| Session Security | ✅ | Secure, HTTP-only cookies |
| Input Validation | ✅ | WTForms validators |
| SQL Injection | ✅ | SQLAlchemy ORM (parameterized queries) |
| XSS Prevention | ✅ | Jinja2 auto-escaping |

### Configuration

```bash
# Required environment variable
SECRET_KEY=your-random-secret-key-here

# Set to production for additional security
FLASK_ENV=production
```

---

## Known Security Considerations

### SQLite Limitations

For production deployments with sensitive data:

1. **Database File**: SQLite stores data in a single file. Ensure proper file permissions.
2. **Concurrent Access**: SQLite has limited write concurrency. For high-traffic sites, consider PostgreSQL.
3. **Backups**: Regularly backup the database file.

### Session Security

- Sessions are stored client-side (signed cookies)
- `SECRET_KEY` must be kept secure and random
- Session cookies are configured with:
  - `Secure=True` (HTTPS only in production)
  - `HttpOnly=True` (JavaScript inaccessible)
  - `SameSite=Lax` (CSRF protection)

### Rate Limiting

Current limits on auth routes:

- Login: 5 attempts per minute per IP
- Register: 3 attempts per minute per IP

For production, consider:
- Lower limits for sensitive operations
- IP-based and account-based limiting
- Temporary account lockouts

---

## Security Best Practices

### For Users

1. **Use a strong password**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - Avoid common passwords

2. **Keep your secret key private**
   - Never commit `SECRET_KEY` to version control
   - Use environment variables

3. **Enable HTTPS**
   - Essential for protecting login credentials
   - Free certificates available via Let's Encrypt

### For Deployers

1. **Environment Variables**
   ```bash
   # Generate a secure key
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Firewall Configuration**
   ```bash
   # Allow only HTTP/HTTPS
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw deny 8080  # Unless needed for direct access
   ```

3. **Regular Updates**
   ```bash
   # Keep dependencies updated
   pip install -r requirements.txt --upgrade
   
   # Check for known vulnerabilities
   pip install safety
   safety check
   ```

4. **Monitoring**
   - Set up log monitoring
   - Configure alerts for suspicious activity
   - Review access logs regularly

---

## Security Headers

For enhanced security, configure your reverse proxy to include:

```
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

Example Nginx configuration:

```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

---

## Incident Response

If a security incident occurs:

1. **Contain**: Isolate affected systems
2. **Assess**: Determine scope and impact
3. **Report**: Contact security@example.com
4. **Remediate**: Apply fixes
5. **Review**: Post-mortem and improvements

---

## Thanks

Thank you for helping keep SampleSplit secure!
