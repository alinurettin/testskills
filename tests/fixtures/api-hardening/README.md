# Independent schema outcomes

`schema-oracle.json` is a selected snapshot of the MIT-licensed
[JSON Schema Test Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite),
retrieved 2026-10-22. Each group records its source URL. The 69 expected outcomes
come from the independent upstream suite, not from QA Suite's generator or checker.
The original license is included here.

Selection: all draft2020-12 oneOf, allOf, exclusiveMinimum groups, and the
additionalProperties groups that use the documented subset (schema/by itself/
default/applicators/null values). Unsupported patternProperties/propertyNames/
dependentSchemas groups are not presented as passing coverage; separate tests
require an explicit UNVERIFIED result for unsupported assertions.

Both Python and the distributed TypeScript helper consume the same fixed oracle.
Generator tests separately assert numeric, length and item-count invariants using
plain predicates; they do not call the generator's validator to compute expectations.
No package installation or runtime network access is needed.
