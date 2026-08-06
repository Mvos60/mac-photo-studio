# MPS Project State

## 1. Snapshot

**Last verified:** 2026-08-06  
**Project:** Mac Photo Studio  
**Repository:** `~/Projects/mac-photo-studio`  
**Branch:** `main`  
**Remote:** `origin/main`  
**Version:** `0.2.1rc2`  
**Baseline HEAD before Sprint 015.14D.2:** `f3885aa`  
**Baseline commit:** `Sprint 015.14D.1.6: Align and wrap import summary values`

Bij aanmaak van dit document was:

- local `main` gelijk aan `origin/main`;
- de working tree schoon;
- de laatst volledig geverifieerde suite `868 passed`.

Dit bestand maakt zelf deel uit van de nog ongecommitte Sprint 015.14D.2-documentatie. Controleer altijd de werkelijke Git-status.

## 2. Huidige productstatus

De native GUI-import werkt en ondersteunt:

- calendar-first destination selection;
- RAW en JPG op afzonderlijke media;
- Resume, Start new en Cancel;
- beschermde state replacement;
- Stop and Resume Later;
- duplicate-media recognition;
- per-file `VERIFIED`, `SKIPPED`, `FAILED`;
- native voortgang en resultaten;
- final reconciliation;
- verwijderen van active state na succesvolle completion;
- groene System Status na succesvolle afronding;
- goedgekeurde camerabranding in main GUI en About.

De CLI blijft ondersteund.

## 3. Canonieke paden

Photo archive:

```text
/home/mac/Pictures
```

Active import state:

```text
/home/mac/.local/state/mac-photo-studio/active_import_session.json
```

Configuration:

```text
/home/mac/.config/mac-photo-studio/settings.yaml
```

Launcher:

```text
/home/mac/.local/bin/mac-photo-studio
```

De launcher gebruikt de live checkout in:

```text
/home/mac/Projects/mac-photo-studio
```

## 4. Destinationmodel

```text
PHOTOS_ROOT/YEAR/MM/DD[_DESCRIPTION]/PROJECT
```

Een geldige structured Resume hergebruikt opgeslagen destination en selection exact.

Een gecontroleerde praktijktest bevestigde dat de huidige Resume-routing correct werkt. Open dit niet opnieuw als defect zonder een nieuwe reproduceerbare test.

## 5. Laatst afgeronde productsprint

### Sprint 015.14D.1.6 / D.1.7

Opgelost:

- verticale mismatch tussen summarylabels en waarden;
- clipping van lange Session ID- en Destinationwaarden.

Gewijzigd:

```text
mps/gui/import_window.py
tests/test_import_window.py
```

Verificatie:

```text
compileall: passed
ImportWindow: 26 passed
full pytest: 868 passed
git diff --check: passed
GUI inspection by Mac: passed
```

Commit:

```text
f3885aa Sprint 015.14D.1.6: Align and wrap import summary values
```

## 6. Huidige documentatiesprint

### Sprint 015.14D.2 — Integrate Codex guidance and project handoff

Bedoelde repositorywijzigingen:

```text
M  AGENTS.md
A  docs/assistant/MPS_WORKING_AGREEMENT.md
A  docs/assistant/MPS_PROJECT_STATE.md
```

Daarnaast wordt een compacte globale Codex-instructie voorbereid. Een bestaande `~/.codex/AGENTS.md` wordt nooit blind overschreven.

Deze sprint wijzigt geen Python-code, foto's, configuratie, sessiestaat of testmedia.

Voor deze uitsluitend documentaire wijziging zijn compileall en pytest niet vereist. Wel vereist:

```text
git diff --check
git status --short
inhoudelijke review door Mac
```

Commit en push pas na expliciete goedkeuring.

## 7. Normale testomgeving

Normale scanroots:

```text
/media
/run/media
/mnt
```

Tijdelijke MPS-TestMedia-roots zijn niet actief.

Er hoort geen actieve test-importsessie te bestaan.

Testkit blijft beschikbaar in:

```text
/home/mac/MPS-TestMedia
```

Inspecteer de actuele ronde voordat testmedia opnieuw worden gebruikt.

## 8. Herbruikbare testfotokit

Locatie:

```text
/home/mac/MPS-TestMedia
```

De bronset bestaat uit vier herbruikbare foto's, ieder als RAW+JPG-paar:

```text
4 × ARW
4 × JPG
```

Helper:

```text
/home/mac/MPS-TestMedia/mps-test-media.sh
```

Nieuwe ronde:

```bash
~/MPS-TestMedia/mps-test-media.sh next
```

De helper gebruikt de bestaande refresh- en nummeringslogica, zodat dezelfde
vier foto's opnieuw kunnen worden gebruikt zonder telkens handmatig nieuwe
testbestanden klaar te zetten.

Inspecteer de actuele ronde vóór gebruik en behoud bronset en generator.

## 9. Branding

Canonical asset:

```text
mps/assets/branding/mps-camera-512.png
```

Display assets:

```text
mps/assets/branding/display/mps-camera-dark-96.png
mps/assets/branding/display/mps-camera-dark-144.png
```

Slogan:

```text
Real Photography. Proven.
```

Niet wijzigen buiten een brandingsprint.

## 10. Relevante open requirements

Verifieer vóór implementatie; sommige kunnen al deels opgelost zijn:

- `.Trash*` en duidelijke systeem-/trashmappen niet importeren;
- een ontbrekend cullingpad is een fout;
- path separators mogen geen onverwachte directories maken;
- gebruik de geconfigureerde archive root;
- CLI-import blijft intact;
- gettext-compatible localization readiness;
- toekomstige talen: NL, EN, DE, FR.

## 11. Volgende productsprint

### Sprint 015.14E — Native import cleanup and finalization

Begin read-only.

Inspecteer:

- resterende GUI-terminal-importcode;
- CLI-only terminalhelpers;
- bewezen dode fallbacks;
- controller- en worker lifecycle;
- dialog cleanup;
- stale process tracking;
- documentatie;
- packaging/launcher;
- release-readiness.

Kritieke grens:

```text
Do not remove CLI import support.
```

Na inspectie eerst een klein voorstel; nog geen implementatie zonder goedkeuring.

## 12. Eerste verificatie in een nieuwe sessie

```bash
cd ~/Projects/mac-photo-studio
git status
git branch --show-current
git log -1 --oneline
git branch -vv
```

Als werkelijkheid en dit document verschillen, meld het verschil en forceer niets terug.

Voor onze accountant is geen citroen zuur genoeg.
