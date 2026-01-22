# Acceptable Use Policy

**Policy ID:** AUP-001  
**Version:** 1.0  
**Effective Date:** 2025-01-XX  
**Review Frequency:** Annually  
**Owner:** Development Team

---

## 1. Purpose

This policy defines acceptable use of Parlay Gorilla systems and services, ensuring that users and administrators use systems responsibly and in compliance with applicable laws and regulations.

---

## 2. Scope

This policy applies to:
- **End Users:** Application users (customers)
- **Administrators:** System administrators, developers
- **Third Parties:** Vendors, contractors with system access

---

## 3. Acceptable Use

### 3.1 Authorized Use

**Users may:**
- Access and use Parlay Gorilla for its intended purpose (sports betting parlay generation and analysis)
- Create and manage their own accounts
- Generate parlays and analyses
- Share parlays with other users (via share functionality)
- Access their own data and analytics

**Administrators may:**
- Access systems for legitimate business purposes
- Perform system administration tasks
- Monitor system performance and security
- Respond to user support requests

### 3.2 Prohibited Use

**Users and administrators are prohibited from:**
- Attempting to gain unauthorized access to systems or data
- Attempting to bypass authentication or authorization controls
- Attempting to exploit vulnerabilities
- Interfering with system operations or performance
- Using systems for illegal activities
- Sharing account credentials
- Creating multiple accounts to circumvent usage limits
- Scraping or automated data collection without permission
- Reverse engineering or decompiling application code
- Introducing malware or malicious code

---

## 4. Account Security

### 4.1 User Responsibilities

**Users must:**
- Keep account credentials confidential
- Use strong passwords (when enforced)
- Not share account credentials
- Report suspected security incidents
- Log out when finished using the application

**Users are responsible for:**
- All activities under their account
- Maintaining account security
- Reporting unauthorized access

### 4.2 Administrator Responsibilities

**Administrators must:**
- Use strong, unique passwords
- Enable multi-factor authentication (when available)
- Not share administrative credentials
- Use principle of least privilege
- Log all administrative actions

---

## 5. Data Protection

### 5.1 User Data

**Users must not:**
- Access other users' data without authorization
- Attempt to extract or export other users' data
- Use data for unauthorized purposes

**Administrators must:**
- Access user data only for legitimate business purposes
- Maintain confidentiality of user data
- Follow data retention and deletion policies
- Not share user data with unauthorized parties

### 5.2 Payment Data

**Users must not:**
- Attempt to access payment processing systems
- Attempt to manipulate payment data
- Share payment information insecurely

**Administrators must:**
- Access payment data only for legitimate business purposes (reconciliation, support)
- Maintain confidentiality of payment data
- Follow PCI DSS requirements (Stripe handles card data)

---

## 6. System Access

### 6.1 Authorized Access

**Users:**
- Access via web application (https://www.parlaygorilla.com)
- Authentication required for protected features
- Role-based access (user/mod/admin)

**Administrators:**
- Access via Render dashboard (infrastructure)
- Access via GitHub (source code)
- Access via application admin interface
- Authentication and authorization required

### 6.2 Unauthorized Access

**Prohibited:**
- Attempting to access systems without authorization
- Attempting to bypass authentication
- Attempting to escalate privileges
- Attempting to access other users' accounts

**Consequences:**
- Account suspension or termination
- Legal action if applicable
- Reporting to law enforcement if criminal activity

---

## 7. Monitoring and Enforcement

### 7.1 Monitoring

**Systems are monitored for:**
- Unauthorized access attempts
- Suspicious activity
- Policy violations
- Security incidents

**Monitoring Methods:**
- Application logs (`system_logs` table)
- Authentication logs
- Payment event logs
- Infrastructure logs (Render)

### 7.2 Enforcement

**Violations may result in:**
- Warning notification
- Account suspension
- Account termination
- Legal action
- Reporting to law enforcement

**Enforcement Process:**
1. Detect violation
2. Investigate violation
3. Determine appropriate action
4. Execute action
5. Document violation and action

---

## 8. Reporting Violations

### 8.1 User Reporting

**Users may report:**
- Suspected security incidents
- Policy violations
- Unauthorized access
- Suspicious activity

**Reporting Methods:**
- Email: [To be filled]
- In-app support: [If available]
- Security reporting: See `SECURITY.md`

### 8.2 Administrator Reporting

**Administrators must report:**
- Security incidents
- Policy violations
- Unauthorized access
- System compromises

**Reporting Process:**
- See `incident_response_plan.md` for detailed procedures

---

## 9. Compliance

### 9.1 Legal Compliance

**Users and administrators must comply with:**
- Applicable laws and regulations
- Terms of service
- Privacy policy
- This acceptable use policy

### 9.2 Regulatory Compliance

**This policy supports:**
- SOC 2 Type I compliance
- Data protection regulations (GDPR, CCPA if applicable)
- Payment card industry requirements (PCI DSS via Stripe)

---

## 10. Policy Updates

### 10.1 Notification

**Users will be notified of:**
- Significant policy changes
- New prohibited activities
- Updated enforcement procedures

**Notification Methods:**
- Email notification
- In-app notification
- Policy update date in policy document

### 10.2 Acceptance

**Users accept this policy by:**
- Creating an account
- Using the application
- Continuing to use the application after policy updates

---

## 11. Contact

**Policy Questions:**
- Email: [To be filled]
- Support: [To be filled]

**Security Incidents:**
- See `SECURITY.md` for reporting procedures

---

## 12. Policy Review

This policy is reviewed annually or when:
- Legal requirements change
- New threats identified
- Significant incidents occur

---

**Approved By:** [To be filled]  
**Last Review Date:** [To be filled]  
**Next Review Date:** [To be filled]
