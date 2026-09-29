# Rewriting requirements: EARS patterns, user stories, acceptance criteria

Use these patterns when you **propose** a clearer version of a requirement. Put the proposal in `notes` or `acceptance_criteria`, or give it as a suggestion in the report. Never overwrite the stakeholder's original `text` without their agreement.

## Contents
1. EARS patterns (EN + TR)
2. User stories and INVEST
3. Acceptance criteria formats
4. Before/after examples

---

## 1. EARS patterns (Easy Approach to Requirements Syntax)

EARS was developed by Mavin et al. at Rolls-Royce (2009). Each pattern makes the trigger, condition and response explicit, which translates directly into test preconditions, actions and expected results.

| Pattern | English template | Turkish template | Test mapping |
|---|---|---|---|
| Ubiquitous | The `<system>` shall `<response>`. | `<Sistem>`, `<yanıt>` -malıdır. | Always-true check |
| Event-driven | **When** `<trigger>`, the `<system>` shall `<response>`. | `<Tetikleyici>` **olduğunda**, `<sistem>` `<yanıt>` -malıdır. | Action = trigger |
| State-driven | **While** `<state>`, the `<system>` shall `<response>`. | `<Durum>` **süresince/iken**, `<sistem>` … -malıdır. | Precondition = state |
| Unwanted behaviour | **If** `<unwanted condition>`, **then** the `<system>` shall `<response>`. | **Eğer** `<istenmeyen durum>` **ise**, `<sistem>` … -malıdır. | Negative test |
| Optional feature | **Where** `<feature is included>`, the `<system>` shall `<response>`. | `<Özellik>` **etkin olduğunda/bulunduğu durumda**, … | Configuration or feature-flag test |
| Complex | **While** `<state>`, **when** `<trigger>`, the `<system>` shall … | `<Durum>` iken `<tetikleyici>` olduğunda … | Combined |

Every "When" requirement should have a matching "If … then" requirement for its failure. When the failure case is missing, that is a completeness finding.

## 2. User stories and INVEST

The template is: *As a `<role>`, I want `<capability>`, so that `<benefit>`.* In Turkish: *`<Rol>` olarak, `<yetenek>` istiyorum, böylece `<fayda>`.*

Check each story against INVEST:

- **I**ndependent: Can it be delivered and tested without another story? If not, note the dependency.
- **N**egotiable: Does it describe a need rather than a fixed solution?
- **V**aluable: Is the benefit clause present and real?
- **E**stimable: Does the team understand it well enough to size it? If not, there are open questions.
- **S**mall: Does it fit in one iteration? If not, propose splitting it by workflow step, business rule, data variation or interface.
- **T**estable: Does it have acceptance criteria with observable outcomes?

## 3. Acceptance criteria formats

**Scenario-oriented (Gherkin).** Keep 3–5 steps, use declarative language (what, not how clicks happen), and one behaviour per scenario.

```gherkin
# language: en
Scenario: Coupon applied at the exact minimum basket amount
  Given a registered customer with a basket total of 100.00 TRY
  When they apply the active coupon "SUMMER10"
  Then the basket total becomes 90.00 TRY
```

```gherkin
# language: tr
Senaryo: Asgari sepet tutarında kupon uygulanması
  Diyelim ki kayıtlı müşterinin sepet toplamı 100,00 TL
  Eğer ki aktif "YAZ10" kuponunu uygularsa
  O zaman sepet toplamı 90,00 TL olur
```

Turkish Gherkin keywords: `Özellik` (Feature), `Kural` (Rule), `Geçmiş` (Background), `Senaryo` (Scenario), `Senaryo taslağı` (Scenario Outline), `Örnekler` (Examples), `Diyelim ki` (Given), `Eğer ki` (When), `O zaman` (Then), `Ve` (And), `Fakat` (But).

**Rule-oriented.** Use a bullet list or an input → output table. This is better for many data variations:

| Basket total | Customer type | Coupon | Result |
|---|---|---|---|
| < 100 TL | any | YAZ10 | Rejected: "Minimum 100 TL" |
| ≥ 100 TL | registered | YAZ10 | 10% discount |
| ≥ 100 TL | guest | YAZ10 | Rejected: "Log in required" |

Good acceptance criteria cover the happy path, at least one failure path, and the boundaries.

## 4. Before/after examples

| Before | Problems | After (proposal) |
|---|---|---|
| "The system should respond quickly." | vague, weak modal, no conditions | "When a user submits the search form, the system shall display results within 1.0 s at p95 with 100 concurrent users." |
| "Kullanıcı şifresini değiştirebilir ve e-posta alır." | compound, trigger unclear | REQ-a: "Kullanıcı profil sayfasından şifresini değiştirebilmelidir." REQ-b: "Şifre değiştirildiğinde, sistem kullanıcıya 1 dakika içinde bildirim e-postası göndermelidir." |
| "Invalid files must not be uploaded." | negative, 'invalid' undefined | "If the uploaded file is not PDF/PNG/JPG or exceeds 10 MB, then the system shall reject it and display 'Only PDF, PNG, JPG up to 10 MB are allowed'." |
| "Raporlar mümkünse Excel'e aktarılabilmelidir." | escape clause, format undefined | "Kullanıcı rapor ekranından sonuçları .xlsx formatında (en fazla 100.000 satır) dışa aktarabilmelidir." |
