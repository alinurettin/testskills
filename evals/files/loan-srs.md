# Loan Application – SRS excerpt v0.3

- FR-1 The applicant must be between 18 and 65 years old.
- FR-2 The loan amount shall be between 1,000 and 50,000 EUR.
- FR-3 Applications with a credit score below 500 are rejected; 500-699 go to manual review; 700 and above are auto-approved.
- FR-4 Applicants over 21 can apply online; others must visit a branch.
- FR-5 The system should process applications quickly and notify the applicant by e-mail, SMS etc.
- FR-6 Application status flow: Draft → Submitted → In Review → Approved / Rejected. Submitted applications can be withdrawn.
- FR-7 The interest rate is TBD by the finance team.
- NFR-1 The system must be secure and highly available.
