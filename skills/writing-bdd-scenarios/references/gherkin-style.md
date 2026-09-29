# Gherkin style guide (TR / EN)

## Contents
1. From the generated draft to a good scenario
2. Rules
3. Turkish phrasing
4. Scenario Outline and Examples
5. Tags

---

## 1. From the generated draft to a good scenario
`generate_features.py` writes a **faithful but imperative** draft, with one When/Then pair per manual step. Rewrite it into **declarative** business language: describe *what* the user achieves, not *how* they click. Keep every tag.

**Draft (imperative):**
```gherkin
  @TC-003 @high @regression
  Senaryo: TC-003 Kupon 100,00 TL sınırında uygulanır
    Diyelim ki Sepette 100,00 TL tutarında ürün var
    Eğer ki 'Kupon kodu' alanına kodu yaz, 'Uygula'ya tıkla "YAZ10"
    O zaman 'Kupon uygulandı.' mesajı görünür
    Eğer ki Sipariş özetini kontrol et
    O zaman İndirim -10,00 TL; ödenecek tutar 90,00 TL
```

**Rewritten (declarative):**
```gherkin
  @TC-003 @high @regression
  Senaryo: TC-003 Kupon 100,00 TL sınırında uygulanır
    Diyelim ki sepet tutarı "100,00" TL
    Eğer ki "YAZ10" kuponunu uygularsam
    O zaman "Kupon uygulandı." mesajını görürüm
    Ve indirim "-10,00 TL", ödenecek tutar "90,00 TL" olur
```

## 2. Rules
1. **One behaviour per scenario.** The title says which rule and condition it proves; keep the `TC-###` prefix.
2. **3–5 steps.** Given builds the context, When is the single triggering action, Then covers the observable outcome(s). Several When/Then pairs usually mean two scenarios. Split them, or keep them only when the manual test is a deliberate flow (use case).
3. **Declarative, not UI mechanics.** Write "Eğer ki kuponu uygularsam", not "Uygula butonuna tıklarsam". UI details live in page objects and step definitions.
4. **Concrete, quoted values** for anything a step definition captures: amounts, codes, messages. Quoted values map to `{string}` parameters.
5. **Background only for context true for every scenario** in the feature: the active coupon, the logged-in user. Never put actions in the Background.
6. **Reusable step phrases.** The same meaning always uses the same sentence, so one step definition serves many scenarios. Check existing step definitions before inventing new wording.
7. **No conjunctions inside a step** ("... ve ... ve ..."). Use `Ve` / `And` lines.
8. **Then steps assert outcomes the business cares about**: message, amount, status, sent email. They do not assert technical internals.
9. **Keep the expected results of the manual test.** Rewriting the wording must not change *what* is verified.

## 3. Turkish phrasing
- Keywords (`# language: tr` on the first line):
  - `Özellik` (Feature), `Kural` (Rule), `Geçmiş` (Background)
  - `Senaryo` (Scenario), `Senaryo taslağı` (Scenario Outline), `Örnekler` (Examples)
  - `Diyelim ki` (Given), `Eğer ki` (When), `O zaman` (Then), `Ve` (And), `Fakat` (But)
- **Consistent person.** Either first person ("uygularsam", "görürüm") or third person ("kullanıcı uygularsa", "sistem gösterir"). Do not mix them within one project.
- **Conditional suffixes read naturally after `Eğer ki`:** "-rsam/-rsem", "-rsa/-rse".
- **Numbers and money in Turkish format** inside quotes: `"1.234,56 TL"`. Step definitions receive them as strings; parse them explicitly if arithmetic is needed.

## 4. Scenario Outline and Examples
- Use an outline for data variants of one behaviour: BVA values, decision-table columns, pairwise application parameters. The generator creates **one tagged `Examples`/`Örnekler` block per test case**, so every row keeps its `@TC-###` tag. Keep that structure.
- Name the outline `<id> <title>`, so each generated test title starts with the TC ID.
- Merge the `pre`/`d#`/`e#` columns into meaningful columns while rewriting, e.g. `| id | title | sepet | indirim | ödenecek |`.

## 5. Tags
- `@REQ-###` goes on the Feature. `@TC-###`, `@<priority>`, `@smoke`, `@regression` and `@negative` go on the scenario or examples block.
- playwright-bdd turns Gherkin tags into Playwright tags. The results loop (`pw_results.py`) and `--grep @TC-003` then work exactly as for plain specs.
- For known product bugs, playwright-bdd supports special tags such as `@fail` and `@fixme`. Use `@fail` together with the defect key tag, e.g. `@fail @SHOP-481`.
