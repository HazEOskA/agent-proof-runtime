# Architecture Lock v0.1

Status: **LOCKED FOR IMPLEMENTATION**

Zakres: pierwszy pionowy przebieg Agent Proof Runtime

## 1. Cel

Udowodnić najkrótszy sensowny przepływ produktu:

1. kontroler tworzy świeży workspace,
2. uruchamia jednego deterministycznego agenta demonstracyjnego,
3. agent tworzy artefakt i wykonuje test,
4. kontroler buduje łańcuch zdarzeń oraz korzeń Merkle,
5. zapisuje `proof-bundle.json`,
6. niezależny validator liczy wszystko ponownie,
7. operator dostaje czytelny `report.html`.

## 2. Poza zakresem v0.1

- wykonywanie dowolnego, niezaufanego kodu,
- blokada sieci egzekwowana przez kernel,
- Docker, gVisor, Firecracker, TEE i TPM,
- Trillian lub inny zdalny append-only log,
- PKCS#11, SoftHSM i podpis HSM,
- przechwytywanie syscalli,
- twierdzenia o zgodności bankowej lub non-repudiation.

Te elementy są roadmapą, a nie ukrytymi obietnicami bieżącego kodu.

## 3. Narzędzia i repozytorium

- język: Python 3.11+,
- runtime dependencies: brak,
- testy: `unittest` ze standardowej biblioteki,
- CLI: `apr`,
- kod: `src/agent_proof_runtime`,
- testy: `tests`,
- dokumentacja: `docs`,
- CI: GitHub Actions dla Pythona 3.11 i 3.12.

## 4. Backend wykonawczy

`LocalProcessSandbox` uruchamia wyłącznie wbudowanego workera demonstracyjnego:

- w nowym katalogu tymczasowym,
- ze stałą listą argumentów procesu,
- z minimalnym środowiskiem,
- z limitem czasu,
- z limitami CPU, rozmiaru pliku i liczby deskryptorów na Linuksie,
- bez kopiowania symlinków,
- z limitem liczby i łącznego rozmiaru artefaktów.

Klasa ma jawne oznaczenie `development-only`. To separacja operacyjna, ale nie
granica bezpieczeństwa wobec złośliwego kodu. Interfejs zostawia miejsce na backend
gVisor/microVM bez zmiany formatu dowodu.

## 5. Profil kanonikalizacji

Nazwa profilu: `RFC8785-JCS-INTEGER-PROFILE-v1`.

Bundle używa podzbioru JCS wystarczającego dla bieżącego schematu:

- `null`, boolean, string, tablica, obiekt i bezpieczne liczby całkowite,
- klucze obiektów są stringami i są sortowane leksykograficznie,
- UTF-8 bez ASCII-escape dla zwykłych znaków Unicode,
- brak zbędnych spacji,
- liczby zmiennoprzecinkowe są odrzucane,
- liczby całkowite są ograniczone do zakresu bezpiecznego IEEE-754.

To nie jest deklaracja obsługi całego RFC 8785. Przed formatem publicznym należy
dodać pełne wektory zgodności JCS albo użyć niezależnie audytowanej implementacji.

## 6. Łańcuch zdarzeń

Dla każdego zdarzenia `N` liczone są:

```text
input_hash   = SHA256(C14N(input))
output_hash  = SHA256(C14N(output))
details_hash = SHA256(C14N(details))
```

Następnie:

```text
step_payload = {
  details_hash,
  input_hash,
  output_hash,
  previous_step_hash,
  step_index,
  type
}

step_hash = SHA256(C14N(step_payload))
```

Dla pierwszego kroku `previous_step_hash` to 32 bajty zer zapisane jako hex z
prefiksem `sha256:`. Timestampy nie uczestniczą w łańcuchu.

## 7. Drzewo Merkle

Liść i węzeł są liczone zgodnie z RFC 6962 §2.1:

```text
leaf = SHA256(0x00 || raw_step_hash)
node = SHA256(0x01 || left || right)
```

Drzewo nie duplikuje ostatniego liścia. Dla pustego drzewa root to `SHA256("")`.

## 8. Proof Bundle

Najważniejsze pola:

- `schema_version`,
- `run` — identyfikator, czas, backend i jawny poziom bezpieczeństwa,
- `events` — dane zdarzeń i wszystkie hashe łańcucha,
- `artifacts` — relatywna ścieżka, rozmiar i SHA-256,
- `validation` — wynik testu workera,
- `integrity.event_merkle_root`,
- `integrity.bundle_hash`.

`bundle_hash` to SHA-256 kanonicznego bundle po usunięciu wyłącznie pola
`integrity.bundle_hash`. Chroni przed przypadkową lub prostą manipulacją całym
plikiem, ale bez podpisu nie broni przed atakującym, który może wszystko przeliczyć.

## 9. Przepływ walidacji

Validator nie ufa wynikowi zapisanemu przez runtime. Samodzielnie:

1. sprawdza schemat i dozwolone klucze,
2. przelicza `bundle_hash`,
3. przelicza hashe danych oraz cały hash chain,
4. przelicza korzeń Merkle,
5. blokuje absolutne ścieżki, `..` i symlinki,
6. ponownie hashuje każdy artefakt,
7. sprawdza spójność krytycznych metadanych z hashowanymi zdarzeniami.

Wynik to `LOCAL_VERIFIED` albo `FAILED`. `ANCHORED` jest niedozwolony w v0.1.

## 10. Uruchomienie, wdrożenie i rollback

Uruchomienie lokalne:

```bash
PYTHONPATH=src python -m agent_proof_runtime demo --output .runs/demo
PYTHONPATH=src python -m agent_proof_runtime verify .runs/demo/proof-bundle.json
```

Wdrożenie v0.1 oznacza wyłącznie instalację pakietu CLI w kontrolowanym labie.
Nie ma produkcyjnego deploymentu ani migracji danych.

Rollback:

- odinstalować pakiet lub wrócić do wcześniejszego commita,
- usunąć katalog konkretnego runu,
- nie ma zewnętrznego stanu, bazy ani kluczy do cofania.

## 11. Kryteria akceptacji

- poprawny demo run kończy się `LOCAL_VERIFIED`,
- zmiana artefaktu kończy się `FAILED`,
- zmiana danych zdarzenia kończy się `FAILED`,
- zmiana metadanych bundle kończy się `FAILED`,
- próba wyjścia ścieżką artefaktu poza katalog runu kończy się `FAILED`,
- testy przechodzą na Pythonie 3.11 i 3.12.
