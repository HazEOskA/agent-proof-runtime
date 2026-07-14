# Architecture Lock v0.2 — Mission Runner

Status: **LOCKED FOR IMPLEMENTATION**

## Cel

Oddzielić sandbox od konkretnego systemu agentowego. Ratio Essendi, prosty skrypt
Pythona i przyszłe runtime'y mają być workloadami opisanymi tym samym `MissionSpec`.

## Kontrakt

`apr.mission.v0.2` deklaruje:

- identyfikator misji,
- backend `local-demo` albo `gvisor`,
- workload wbudowany albo komendę kontenera,
- limity czasu, pamięci, CPU i procesów,
- politykę sieci `none`,
- limit oraz wymagalność artefaktów.

Parser odrzuca nieznane pola, duplikaty kluczy, floaty, niebezpieczne ścieżki,
nieprzypięte obrazy i nieobsługiwane kombinacje backend/workload.

## Backendy

### local-demo

- uruchamia wyłącznie workera dostarczonego z APR,
- nie przyjmuje dowolnej komendy,
- zachowuje oznaczenie `development-only`,
- służy do testu pełnego przepływu bez Dockera.

### gvisor

- wymaga Dockera z runtime `runsc`,
- uruchamia tylko obraz przypięty digestem SHA-256,
- używa `--pull=never`, więc runtime nie pobiera obrazu niejawnie,
- blokuje sieć przez `--network=none`,
- używa read-only root filesystem, pustych capabilities i `no-new-privileges`,
- limituje pamięć, CPU, PID-y i czas,
- montuje kopię źródeł tylko do odczytu, nigdy oryginał,
- pozwala pisać wyłącznie do `/output` i efemerycznego `/tmp`,
- monitoruje liczbę oraz rozmiar artefaktów podczas wykonania i zabija kontener po
  przekroczeniu polityki,
- przy braku któregokolwiek wymagania kończy się fail-closed.

## Granica zaufania

gVisor daje realną granicę izolacji procesu, ale v0.2 nadal nie zapewnia zewnętrznej
niezaprzeczalności. Host runtime może zmienić Proof Bundle, dopóki nie dodamy
zdalnej kotwicy lub podpisu kluczem znajdującym się poza hostem.

## Brak sekretów

MissionSpec v0.2 nie przyjmuje zmiennych środowiskowych ani sekretów. Sekrety będą
później przekazywane przez osobny broker uchwytów, bez umieszczania wartości w
manifeście lub Proof Bundle.

## Kryteria akceptacji

- `apr mission validate missions/demo.json` przechodzi,
- `apr run missions/demo.json` daje zweryfikowany Proof Bundle v0.2,
- dowolna komenda z backendem `local-demo` jest odrzucana,
- obraz bez digestu jest odrzucany,
- źródło z `..` jest odrzucane,
- gVisor bez dostępnego `runsc` nie spada do zwykłego Dockera,
- builder komendy zawiera wszystkie zablokowane polityki,
- validator v0.2 sam odtwarza wynik misji,
- walidacja starych bundle v0.1 nadal działa.

## Źródła implementacyjne

- [gVisor — Docker Quick Start](https://gvisor.dev/docs/user_guide/quick_start/docker/)
- [Docker — `docker container create`](https://docs.docker.com/reference/cli/docker/container/create/)
- [Docker — none network driver](https://docs.docker.com/engine/network/drivers/none/)
- [Docker — security options and resource flags](https://docs.docker.com/reference/cli/docker/container/run/)
