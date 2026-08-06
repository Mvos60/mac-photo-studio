# Projectregels — Mac Photo Studio

## 1. Eerst lezen

Voor iedere taak in deze repository:

1. lees dit `AGENTS.md`;
2. lees `docs/assistant/MPS_WORKING_AGREEMENT.md`;
3. lees `docs/assistant/MPS_PROJECT_STATE.md`;
4. controleer daarna zelf repository, branch, HEAD en working tree.

De actuele repository is leidend wanneer een handoffdocument afwijkt.

## 2. Project en communicatie

- Dit project is **Mac Photo Studio (MPS)**, een Python-applicatie met een Tkinter-GUI voor Ubuntu Linux.
- Communiceer met Mac in beknopt Nederlands, tenzij hij een andere taal gebruikt.
- Werk in kleine, veilige, duidelijk afgebakende sprints.
- Benoem vóór iedere wijziging het doel en de exacte bestanden.
- Geef één duidelijke volgende stap in plaats van een lange handmatige testlijst.
- Scheid Codex-prompts, terminalcommando's en uitleg zichtbaar van elkaar.
- Meld onzekerheid en fouten eerlijk; claim niets zonder bewijs.

## 3. Git en scope veilig houden

- Behoud al het bestaande en niet-gecommitte werk.
- Voer nooit `git reset`, `git clean`, `git stash`, destructieve `git restore` of destructieve `git checkout` uit.
- Commit, tag, push, merge, rebase, branchwissel of remote-wijziging alleen na expliciete goedkeuring van Mac.
- Stage niet zonder goedkeuring wanneer de sprintworkflow om review vóór commit vraagt.
- Vermijd brede refactors en niet-gerelateerde opschoning.
- Wijzig alleen bestanden die nodig zijn voor de goedgekeurde sprint.
- Installeer of update geen pakketten of dependencies zonder expliciete toestemming.
- Gebruik geen netwerktoegang zonder expliciete toestemming.

## 4. Gebruikersdata

- Schrijf standaard niets buiten deze repository.
- Wijzig nooit foto's, fotobibliotheken, aangekoppelde media, `~/.local`, desktoplaunchers, configuratie of sessiestaat tijdens inspectiewerk.
- Een expliciet goedgekeurde praktijktest buiten de repository gebeurt alleen met exacte padcontrole, backup en een afzonderlijk veilig script.
- Geautomatiseerde tests gebruiken tijdelijke testmappen en nooit echte foto's.
- Verwijder of formatteer nooit cameramedia als neveneffect van scanning of import.

## 5. MPS-kernregels

- Canonieke fotobibliotheek: `/home/mac/Pictures`.
- De native GUI-import is de voorkeursroute, maar de ondersteunde CLI-import blijft intact.
- Verwijder terminal-importcode alleen wanneer bewezen is dat die niet meer door GUI of CLI wordt gebruikt.
- RAW+JPG op afzonderlijke kaarten blijft een ondersteund hoofdscenario.
- Kaartscanning negeert `.Trash*` en andere duidelijke systeem-/prullenbakmappen.
- Een bestand is pas `VERIFIED` na succesvolle kopie én checksumcontrole.
- Duplicate prevention, provenance, manifest en chain of custody mogen niet worden verzwakt.
- Een geldige structured Resume gebruikt exact de opgeslagen selectie en bestemming.
- Een niet-bestaand cullingpad is een fout, geen geldige nulrapportage.
- Verwijder orphan RAW-bestanden nooit automatisch.
- Wijzig goedgekeurde branding niet tijdens een ongerelateerde sprint.

## 6. Implementatie

- Inspecteer relevante code en tests voordat je wijzigt.
- Stel eerst de concrete oorzaak vast.
- Kies de kleinste robuuste reparatie.
- Voeg waar praktisch een gerichte regressietest toe die vóór de reparatie zou falen.
- Verander geen test enkel om een fout groen te maken.
- Behoud bestaand gedrag, provenance-veiligheid en sessiestaat, tenzij de sprint die expliciet wijzigt.
- Widgets lezen of muteren sessiebestanden niet rechtstreeks; respecteer controller-, runner- en servicelagen.

## 7. Verificatie

Na codewijzigingen, in deze volgorde:

```bash
python3 -m compileall -q mps tests
python3 -m pytest -q <gerichte tests>
python3 -m pytest -q
git diff --check
git status --short
```

Bij uitsluitend Markdown/documentatie zijn pytest en compileall niet nodig, tenzij de documentatiewijziging packaging, gegenereerde bestanden of testverwachtingen raakt.

- Rapporteer de werkelijk uitgevoerde commando's en exacte resultaten.
- Claim nooit dat een handmatige GUI-test is geslaagd; alleen Mac kan die bevestigen.
- Voor zichtbare GUI-wijzigingen volgt altijd één gerichte praktijktest.
- Toon vóór commit gewijzigde bestanden, tests en `git status`.
- Stop daarna en wacht op goedkeuring van Mac.

## 8. Oplevering

Een sprint is pas af wanneer:

- oorzaak en reparatie aantoonbaar zijn;
- gerichte en volledige vereiste tests groen zijn;
- `git diff --check` groen is;
- relevante GUI-test door Mac is bevestigd;
- gebruikersdata en configuratie veilig zijn;
- alleen bedoelde bestanden zijn gewijzigd;
- documentatie en projectstate zijn bijgewerkt;
- commit en push, indien goedgekeurd, zijn gecontroleerd.

Voor onze accountant is geen citroen zuur genoeg.
