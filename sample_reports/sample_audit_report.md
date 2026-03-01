# Security Audit Report

## Executive Summary

**Overall Risk Level:** High
**Risk Score:** 73.3/100
**Total Findings:** 5

## Security Analysis Visualizations

**Overall Risk Score:** 73.3/100 (High)

### Severity Distribution
![Severity distribution of findings](C:/Users/Admin/AppData/Local/Temp/security_audit_charts/severity_severity_5563fef1b81a8ea850565e446952c4f6_300dpi.png)

### Vulnerability Categories
![Vulnerability categories breakdown](C:/Users/Admin/AppData/Local/Temp/security_audit_charts/category_category_bc0f5338bafceb4c0a74b996a8e88c8d_300dpi.png)

### Findings per File
![Findings distribution across files](C:/Users/Admin/AppData/Local/Temp/security_audit_charts/file_distribution_file_distribution_1414a009906f466e6705417df9d8f91d_300dpi.png)

### Confidence Score Distribution
![Detection confidence score distribution](C:/Users/Admin/AppData/Local/Temp/security_audit_charts/confidence_confidence_41a0db76406de6cc151dd14df342441b_300dpi.png)

### Risk Assessment Meter
![Overall risk assessment meter](C:/Users/Admin/AppData/Local/Temp/security_audit_charts/risk_gauge_risk_gauge_c842f71d3b68ac37d480abf2ccdd00e8_300dpi.png)


## Detailed Findings


### High Severity (2)

#### 1. Hardcoded Credentials

**File:** `src/config.py`

**Description:** Database password hardcoded in configuration file

**Confidence:** 95.0%

---

#### 2. API Key Exposure

**File:** `src/auth.py`

**Description:** AWS access key exposed in source code

**Confidence:** 92.0%

---


### Medium Severity (2)

#### 1. Debug Logging

**File:** `src/utils.py`

**Description:** Debug mode enabled in production environment

**Confidence:** 78.0%

---

#### 2. Hardcoded Credentials

**File:** `src/database.py`

**Description:** Database credentials hardcoded

**Confidence:** 85.0%

---


### Low Severity (1)

#### 1. Weak Cryptography

**File:** `src/crypto.py`

**Description:** MD5 hash used instead of SHA256

**Confidence:** 65.0%

---

