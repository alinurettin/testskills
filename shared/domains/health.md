# Domain pack: Health

Use this pack for patient-facing apps, hospital and clinic systems, appointments, prescriptions, lab results, telehealth and health-data integrations. It lists what to ask and test, not legal or clinical advice. Involve the clinical safety officer and compliance for anything that affects care.

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
| Personal health data (KVKK: health data is a special category; GDPR Art. 9) | Explicit consent or a legal basis, strict access control, access logging, retention, secure transfer, data minimisation |
| National health systems (in Türkiye: Ministry of Health systems such as e-Nabız / USS; SGK MEDULA for reimbursement and e-prescription) | Integration contracts, message validation, error and resend handling, identity matching. Confirm the current integration specifications. |
| Interoperability standards (HL7 v2, HL7 FHIR, DICOM, ICD-10, LOINC, SNOMED CT where used) | Message and resource validation, code-system correctness, units |
| Medical device software (IEC 62304, ISO 14971; EU MDR or the local equivalent when the software is a medical device) | Risk management traceability, software safety classes, verification evidence; the RTM becomes regulatory evidence |
| Accessibility | Patient portals are often subject to accessibility obligations; test against WCAG 2.2 AA |

## 2. Implicit requirements checklist
- **Identity:**
  - patient matching (national ID, foreign patients, newborns without an ID, duplicates);
  - the merge and unmerge of records;
  - proxy access (a parent for a child, a guardian).
- **Consent:** what is consented to, for which purpose, and for how long; withdrawal; emergency override (break-glass) with justification and audit.
- **Access control:**
  - role- and relationship-based access (only the treating clinician);
  - sensitive categories (mental health, HIV, genetic data) with extra restrictions;
  - logging and auditing of every view.
- **Clinical safety:**
  - units and their conversions (mg vs mcg, mmol/L vs mg/dL);
  - dose limits;
  - allergy and interaction alerts (cannot be silently dismissed);
  - abnormal result flags;
  - the time and time zone of observations.
- **Workflow states:**
  - appointment: booked → confirmed → arrived → completed / no-show / cancelled;
  - order and result: ordered → collected → resulted → verified → amended;
  - prescription: prescribed → dispensed → cancelled.
- **Integrations:** acknowledgement handling, retries, duplicate messages, out-of-order results, partial failures. What does the clinician see when a message is pending?
- **Data retention and deletion:** legally required retention periods versus deletion requests. Which rule wins?
- **Notifications:** no sensitive details in SMS or push previews.

## 3. High-risk rules → test design
| Rule shape | Technique |
|---|---|
| Dose, age and weight-based limits, reference ranges | 3-value BVA with units; equivalence classes per unit system |
| Access rules (role × relationship × sensitivity × emergency) | Full decision table; negative tests through the UI and the API; audit assertions |
| Appointment, order, result and prescription lifecycles | State transition with 1-switch plus invalid transitions (amend after verify, dispense after cancel) |
| Message integrations (HL7/FHIR) | Contract and schema validation; error guessing (missing mandatory segment, wrong code system, duplicate or out-of-order message) |
| Patient matching | Classification tree over the identity attributes; near-duplicate data (Turkish characters, transposed dates) |

## 4. Test data
- Fully synthetic patients only (never real or de-identified production data without an approved process). Mark test patients clearly: name prefixes, test-only identity ranges supplied by the environment.
- Edge identities: no national ID, foreign ID, twins with the same birth date, name changes, Turkish characters in names.
- Clinical values right at the thresholds and units, in both unit systems.

## 5. Non-functional focus
- **Availability:** 24/7. Maintenance windows, and the downtime procedures clinicians follow. Recovery with no data loss (RPO close to zero for clinical records).
- **Performance:** morning appointment peaks; result retrieval during rounds.
- **Security:** ASVS L2 minimum, L3 for systems holding large clinical datasets. V8 (authorisation), V14 (data protection), V16 (audit logging).
- **Safety:** fail-safe states (an alert service down → the order is blocked or flagged, never silently allowed). Hazard warnings are visible and unambiguous.
- **Accessibility:** patient portals and appointment booking against WCAG 2.2 AA, including cognitive accessibility (3.3.7, 3.3.8).

## 6. Defects typically found
- A unit mismatch between systems (mg vs mcg) that is not caught at an interface.
- A clinician can open a record outside their care relationship with no audit entry.
- Amended results do not notify the clinician who saw the original.
- Duplicate patients are created by a minor spelling difference; results end up on the wrong record.
- Sensitive details appear in SMS reminders or push notification previews.
