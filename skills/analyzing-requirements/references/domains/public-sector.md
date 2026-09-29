# Domain pack: Public sector and e-government

Use this pack for citizen-facing services, internal government systems, e-signature and official correspondence, applications, permits, payments to institutions, and open data. It lists what to ask and test, not legal advice. Confirm the current versions of the guidelines with the institution's compliance or IT security unit.

## Contents
1. Regulations and standards to check
2. Implicit requirements checklist
3. High-risk rules → test design
4. Test data
5. Non-functional focus
6. Defects typically found

---

## 1. Regulations and standards to check
| Area | What it usually drives |
|---|---|
| E-government integration (in Türkiye: e-Devlet Kapısı login and services) | Authentication via the national gateway, identity attributes received, session handover, error pages when the gateway is unavailable |
| Information and communication security (in Türkiye: the Presidency Digital Transformation Office's Information and Communication Security Guide, and related circulars) | Security controls by asset criticality level, logging, data localisation, supplier requirements. Treat it as a checklist source for security testing. |
| Electronic signature and registered e-mail (in Türkiye: e-signature law No. 5070, KEP) | Signature creation and verification, certificate validity and revocation, timestamps, legal delivery evidence |
| Accessibility obligations for public websites and apps (national rules; the EU Web Accessibility Directive) | WCAG 2.x AA conformance, an accessibility statement, a feedback mechanism |
| Personal data (KVKK / GDPR), right to information | Lawful basis, transparency texts, retention, responses to information requests |
| Archiving and records management | Retention schedules, document formats, disposal rules |

## 2. Implicit requirements checklist
- **Identity and delegation:**
  - citizens, foreigners and legal entities (institutions, companies);
  - acting on behalf of others (guardians, company representatives);
  - authorisation after e-Devlet login.
- **Eligibility rules:** age, residence, income or status conditions. Which data source is authoritative, and what happens when it is unavailable?
- **Deadlines:**
  - application windows (start and end inclusive, time zone);
  - behaviour at the deadline minute;
  - extensions;
  - the system clock as the legal time source.
- **Documents:**
  - upload formats and sizes;
  - verification of e-signed documents;
  - generated official documents with barcode or QR verification;
  - document validity checks.
- **Workflow:**
  - submitted → under review → additional information requested → approved / rejected / appealed;
  - statutory response times;
  - the notification channel (KEP, SMS, e-mail, the e-Devlet inbox).
- **Payments to institutions:** fees and penalties, rounding, receipt generation, refunds.
- **Language and communication:** plain-language requirements, Turkish typography, messages that are legally binding.
- **Transparency:** audit trails of every decision, and who changed what.

## 3. High-risk rules → test design
| Rule shape | Technique |
|---|---|
| Eligibility criteria combinations | Decision table (full coverage); each rejection reason tested and communicated |
| Application and permit lifecycle, appeals | State transition with invalid transitions and statutory deadlines (clock control) |
| Deadline and date rules | BVA on dates and times: the opening and closing minute, leap day, year end, holidays |
| Identity and delegation | CRUD × role × delegation; object-level authorisation (another citizen's application ID) |
| E-signature and document verification | Error guessing: expired, revoked or self-signed certificates; a modified signed document; a wrong document type |

## 4. Test data
- Only synthetic identities supplied by the test environments of the gateway and the institution. Never real citizens' data.
- Edge cases:
  - persons with no data in the authoritative source;
  - foreigners;
  - minors with guardians;
  - companies with several representatives;
  - persons at eligibility boundaries (age exactly at the limit on the deadline date).
- Test certificates for e-signature from the test certificate authority.

## 5. Non-functional focus
- **Performance:** deadline-day peaks (the last hours before a closing time), campaign-style announcements. Spike and stress profiles, and queueing behaviour.
- **Availability and resilience:** behaviour when the national gateway or the authoritative data sources are down. Clear citizen messages, with no lost submissions.
- **Security:** checks from the national security guide by asset level, mapped to ASVS chapters (V6/V7 for authentication and sessions, V8 authorisation, V14 data protection, V16 logging).
- **Accessibility:** a legal obligation in most jurisdictions. Test the full service journeys against WCAG 2.2 AA, including document uploads, CAPTCHAs (3.3.8) and timeouts (2.2.1).

## 6. Defects typically found
- An application is accepted one minute after the deadline because of server vs client time.
- A representative can see or submit another company's applications.
- A rejection reason is not communicated, or is shown only as a code.
- Uploaded e-signed documents are accepted without signature verification.
- The service is unusable with a keyboard or a screen reader at the upload or CAPTCHA step.
