# Compatibility and workflow dependencies / Uyumluluk ve iş akışı bağımlılıkları

| Host / surface | Format and expected capability | End-to-end evidence |
|---|---|---|
| Local Python CLI | Python 3.12/3.13, files, standard library | Local regression suite; see delivery/CI logs for actual OS/runtime |
| Generated API helpers | Node 22.18+/24/26; Playwright for real execution | Mocked distributed TypeScript behavior tests; no live API claim |
| Claude Code | Agent Skills/plugin format, local files and script execution | Historical trials; current actual trigger routing not measured |
| claude.ai / API | Self-contained skill ZIP, environment-dependent execution | Format packaging validation; current host smoke not performed |
| Codex/Cursor/Copilot/Gemini CLI | Agent Skills format plus compatible file/process permissions | Format compatibility only; current host smoke not performed |
| Xray/Zephyr/TestRail/ADO/Qase | Vendor-specific import files | Golden/local checks; live lifecycle checks pending |

The full 17-skill distribution is still the supported complete workflow. Small installations are an advanced selection, not a verified standalone product. Shared Python helpers are copied into each skill by `sync_shared.py` so local script imports do not depend on the entire repository. Workflow handoffs still need other skills:

| Workflow | Working set / dependencies |
|---|---|
| Manual analysis/design/export | analyzing-requirements, designing-test-cases, tracing-requirements, exporting-test-cases; reviewing-test-cases for import/updates; reporting-test-results for closure |
| API lifecycle | testing-apis plus analyzing-requirements, designing-test-cases, tracing-requirements, automating-with-playwright; reporting-test-results for closure |
| Browser/BDD | designing-test-cases, automating-with-playwright, tracing-requirements; writing-bdd-scenarios for Gherkin |
| Orchestrated full process | qa-orchestrator and all skills required by the selected stages |

No reduced bundle has been smoke-tested across hosts. Validate sibling paths, tool permissions, shell/encoding and actual routing before claiming support. `doctor.py` checks the local runtime and project package resolution, not agent activation or cloud host permissions. Core Python work needs no Node or Playwright. Full workflow and platform smoke tests are separate from the proxy routing benchmark.

Türkçe: Dosya biçimi uyumluluğu, belirli bir ajan aracında uçtan uca çalıştırılmış olma anlamına gelmez. Tam akış için 17 skill paketi korunur; küçük kurulumlarda tablodaki görev devirleri ve kardeş dosya yolları ayrıca doğrulanmalıdır. Doctor yalnız yerel çalışma ortamını kontrol eder; skill tetiklenmesini veya bulut izinlerini kanıtlamaz. Denenmeyen platformlar yukarıda açıkça belirtilmiştir.
