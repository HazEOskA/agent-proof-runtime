# Roadmap

## v0.1 — pionowy przebieg lokalny

- disposable workspace,
- agent demonstracyjny,
- artefakt i test,
- hash chain, RFC 6962 Merkle root,
- Proof Bundle, validator i raport HTML.

## v0.2 — użyteczny runner

- jawny manifest misji,
- allowlista narzędzi i limitów,
- adapter agenta bez związania z konkretnym LLM,
- streaming zdarzeń,
- wersjonowany JSON Schema,
- deterministyczne fixture'y interoperacyjności.

## v0.3 — realna granica izolacji

- backend gVisor albo microVM,
- egzekwowana blokada sieci i kontrolowany egress,
- read-only base image i efemeryczny overlay,
- polityka mountów, UID/GID i seccomp,
- testy ucieczki oraz wyczerpania zasobów.

## v0.4 — zaufanie poza hostem runtime

- append-only anchor service na osobnej maszynie,
- receipt z inclusion proof,
- podpis Ed25519 lub PKCS#11,
- rotacja i unieważnianie kluczy,
- statusy `SIGNED_ONLY`, `ANCHORED` i `FAILED` z precyzyjną semantyką.

## v1.0 — profil regulowany

- pełna zgodność JCS RFC 8785 i publiczne test vectors,
- profil in-toto Statement/Predicate,
- sprzętowy HSM i atestacja środowiska,
- model PII oraz HMAC tokenization,
- audyt threat modelu i niezależny przegląd kryptograficzny.
