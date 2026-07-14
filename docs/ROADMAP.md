# Roadmap

## v0.1 — pionowy przebieg lokalny

- disposable workspace,
- agent demonstracyjny,
- artefakt i test,
- hash chain, RFC 6962 Merkle root,
- Proof Bundle, validator i raport HTML.

## v0.2 — Mission Runner (obecny etap)

- ścisły manifest misji,
- adapter workloadu bez związania z konkretnym LLM,
- fail-closed Docker + gVisor command runner,
- blokada sieci, read-only root i limity zasobów,
- Proof Bundle v0.2 z hashem MissionSpec,
- zgodność validatora wstecz z v0.1.

## v0.3 — lab i twarde testy izolacji

- uruchomienie `runsc` na osobnym hoście labowym,
- fixture z realnym przypiętym obrazem,
- testy ucieczki, forka, timeoutu i wyczerpania zasobów,
- eksport zmodyfikowanego workspace jako kontrolowanego artefaktu,
- opcjonalny backend microVM po porównaniu kosztu i czasu startu.

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
