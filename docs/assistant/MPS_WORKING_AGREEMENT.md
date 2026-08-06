# MPS Working Agreement

## 1. Doel en status

Dit document bevat de verdiepende product- en ontwikkelafspraken voor **Mac Photo Studio**.

Bindende korte regels staan in het repositorybestand `AGENTS.md`. De actuele sprintstatus staat in `MPS_PROJECT_STATE.md`.

## 2. Productmissie

MPS is een betrouwbare Linux-applicatie voor foto-ingest en provenance van echte fotografie.

MPS moet:

- cameramedia veilig ontdekken;
- RAW en JPG voorspelbaar koppelen;
- bestanden kopiëren en verifiëren;
- dubbele imports voorkomen;
- chain of custody en provenance bewaren;
- onderbroken imports veilig kunnen hervatten;
- een duidelijke native GUI bieden;
- de geïmporteerde bibliotheek netjes overdragen aan digiKam en Darktable.

Leidend productprincipe:

> Real Photography. Proven.

## 3. Primaire fotografieworkflow

De primaire workflow is gebaseerd op:

- Sony A7 III / ILCE-7M3;
- ARW als RAW-formaat;
- RAW+JPG-opnamen;
- RAW en JPG mogelijk op verschillende kaarten;
- koppeling op gelijke basename;
- RAW als primaire archief- en bewerkingsbron;
- JPG voor snelle referentie, cullingondersteuning en sommige printworkflows.

MPS mag niet afhankelijk worden van cloudopslag, NAS, Apple- of Windows-software, automatische editorstart of één-kaart-only gedrag.

Na import nemen digiKam en Darktable het werk over. MPS start ze niet automatisch zonder een aparte toekomstige beslissing.

## 4. Canonieke paden en bestemming

Canonieke fotobibliotheek:

```text
/home/mac/Pictures
```

Structured destination:

```text
PHOTOS_ROOT/YEAR/MM/DD[_DESCRIPTION]/PROJECT
```

Voorbeeld:

```text
/home/mac/Pictures/2026/08/01_Ljubljana/Adriatic
```

Regels:

- datumcomponenten zijn echte kalenderwaarden;
- description is optioneel;
- project is een aparte laatste component;
- path separators en onveilige tekens worden geweigerd of gesaneerd;
- invoer als `15/07 raw` mag nooit onverwachte submappen maken;
- Resume bewaart en hergebruikt dezelfde structured selection en import root;
- verander deze structuur niet als bijvangst van GUI-polish.

## 5. Media discovery

Card scanning is conservatief en negeert waar van toepassing:

- `.Trash*`;
- verborgen prullenbakmappen;
- filesystemmetadata;
- OS-helpermappen;
- tijdelijke bestanden;
- niet-ondersteunde extensies.

Tests voor scannerwijzigingen dekken ten minste de relevante combinatie van:

- aparte RAW- en JPG-kaarten;
- RAW+JPG op één kaart;
- lege media;
- dubbele media;
- systeem-/trashmappen;
- tijdelijk ontbrekende media;
- herhaalde scans.

Scanning of import wijzigt of formatteert cameramedia nooit automatisch.

Een toekomstige verwijderfunctie voor kaarten moet apart, expliciet bevestigd en zelfstandig beveiligd zijn.

## 6. Pairing

RAW/JPG-koppeling gebruikt gelijke basenames met passende case-insensitive extensieafhandeling.

De pairinglaag onderscheidt:

- complete paren;
- RAW zonder JPG;
- JPG zonder RAW;
- dubbele basenames;
- dubbele inhoud;
- eerder geïmporteerde bestanden.

Kies bij ambiguïteit niet stilzwijgend een bestand.

Pairingwijzigingen mogen duplicate detection, checksumverificatie, import registry, provenance of cullinganalyse niet verzwakken.

## 7. Kopie en verificatie

Normale volgorde:

1. discover;
2. classify;
3. pair;
4. plan;
5. copy;
6. verify;
7. register;
8. record manifest/provenance;
9. report result.

Een bestand is niet succesvol geïmporteerd vóór inhoudsverificatie.

Per-file result:

- `VERIFIED`;
- `SKIPPED`;
- `FAILED`.

Ieder resultaat houdt bron, bestemming, mediatype, status en reden/detail beschikbaar.

Een mislukte kopie wordt nooit als skipped of succesvol gemaskeerd.

## 8. Duplicate prevention

Onbedoelde re-import wordt voorkomen:

- binnen de huidige sessie;
- over de geconfigureerde fotobibliotheek heen.

Een duplicate-skip moet uitlegbaar zijn en steunen op de bewijsvoering van de bestaande architectuur.

Belangrijke scenario's:

- dezelfde bron tweemaal;
- dezelfde inhoud op een ander pad;
- dezelfde basename met andere inhoud;
- eerdere succesvolle import;
- onderbroken import;
- Resume;
- gedeeltelijk verwerkte batch.

## 9. Actieve importsessies

Statebestand:

```text
~/.local/state/mac-photo-studio/active_import_session.json
```

Dit is beschermde gebruikersstaat.

### Resume

Voor een geldige structured sessie:

- gebruik exact de opgeslagen selection;
- gebruik exact de opgeslagen import root;
- open de kalenderselector niet opnieuw;
- valideer vóór hervatten;
- gebruik alleen bij echte legacy state de legacy destinationflow.

### Start new

Bij een bestaande sessie:

- `Start new` is anders dan `Resume`;
- oude state blijft beschermd totdat de eerste nieuwe batch gekopieerd én geverifieerd is;
- annuleren vóór dat moment laat de oude sessie herstelbaar.

### Stop and Resume Later

Deze actie:

- stopt veilig;
- bewaart state;
- laat de sessie hervatbaar;
- veroorzaakt terecht een oranje System Status.

### Completion

`Completed` volgt alleen na succesvolle reconciliation.

Daarna:

- final result meldt succes;
- actieve state verdwijnt;
- System Status wordt groen wanneer geen andere waarschuwing bestaat.

Stopped, failed, canceled of unreconciled is nooit completed.

### State writes

Behoud atomiciteit waar de architectuur die toepast:

- tijdelijke file;
- flush;
- fsync waar relevant;
- atomic replace.

State-schemawijzigingen vereisen compatibiliteit of migratie.

## 10. Native GUI-architectuur

De native GUI-import is de voorkeursroute.

Architectuurgrenzen:

- GUI verzamelt intentie en toont events;
- controller beheert uitvoeringsstatus;
- runner voert workflow uit;
- services laden, valideren en bewaren state;
- interaction adapter vertaalt vragen naar dialogen;
- ImportWindow toont voortgang en resultaten.

Widgets lezen of schrijven state niet rechtstreeks.

Omzeil de controller niet om een dialoogprobleem snel op te lossen.

## 11. GUI-kwaliteit

Controleer bij GUI-wijzigingen:

- baseline/top alignment;
- wrapping zonder clipping;
- echte desktop scaling;
- volledig zichtbare knoppen;
- altijd zichtbare waarschuwing/final result;
- bruikbare minimumafmetingen;
- toetsenbordbediening;
- veilig Escape/close-gedrag;
- maximaal één actieve import;
- geen verweesde terminalvensters;
- geen stale GUI-state.

Kleine zichtbare afwijkingen zijn geldige polishbugs wanneer ze vertrouwen of afwerking raken.

Vergroot niet elk venster als generieke clippingoplossing. Gebruik consistente gridregels en gedeelde layoutconstanten.

## 12. Branding

Goedgekeurde master:

```text
mps/assets/branding/mps-camera-512.png
```

Goedgekeurde displayvarianten:

```text
mps/assets/branding/display/
```

Behoud transparantie, aspect ratio, crop, oranje cage, huidige helderheid en gebruik in header/About.

Slogan:

```text
Real Photography. Proven.
```

Wijzig branding uitsluitend in een expliciete brandingsprint.

## 13. Provenance en chain of custody

Provenance is kernfunctionaliteit.

Behoud:

- stabiele file identity;
- geverifieerde hashes;
- eventvolgorde;
- sessiekoppeling;
- bron-/bestemmingstraceerbaarheid;
- manifestconsistentie;
- chain validation;
- continuïteit bij latere handelingen.

Maak geen provenance-event voor iets dat niet gebeurde.

Herschrijf historische events niet vanwege een presentatiewijziging.

## 14. Culling en quarantine

Analyse is geen verwijdering.

Onderscheid:

- ontbrekende JPG met aanwezige RAW;
- orphan RAW;
- orphan JPG;
- ontbrekend sessiepad;
- ongeldig sessiepad;
- ambigu bestandverband.

Een niet-bestaand sessiepad is een fout.

Verwijder RAW nooit automatisch alleen omdat JPG ontbreekt.

Quarantinehandelingen zijn expliciet, controleerbaar en waar mogelijk herstelbaar.

Quarantine Manager toont geselecteerde bron, werkelijke quarantainelocatie, bewerking en resultaat.

Gebruik de geconfigureerde fotobibliotheek en geen obsolete hardcoded root.

## 15. Configuratie en testmedia

Gebruikersconfiguratie:

```text
~/.config/mac-photo-studio/
```

Normale scanroots:

```text
/media
/run/media
/mnt
```

Voor tijdelijke testroots:

- maak eerst backup;
- voeg alleen bekende roots toe;
- rapporteer exact;
- herstel normale roots na de test;
- verifieer dat testroots verdwenen zijn.

Verwijder testmedia of bestemmingsmappen niet alleen omdat scanroots worden hersteld.

Testmedia blijven gescheiden van productiegegevens. Gebruik geen onvervangbare originelen als destructieve fixture.

Benoem bij praktijktests het scenario: new import, Resume, Start new, duplicate pass, stop/resume of reconciliation.

## 16. Herbruikbare testfotokit

De lokale testfotokit staat buiten de repository op:

```text
/home/mac/MPS-TestMedia
```

De bronset bestaat uit vier foto's. Iedere foto is beschikbaar als RAW+JPG-paar:

```text
4 × ARW
4 × JPG
```

Helper:

```text
/home/mac/MPS-TestMedia/mps-test-media.sh
```

Een nieuwe herkenbare testronde wordt voorbereid met:

```bash
~/MPS-TestMedia/mps-test-media.sh next
```

De helper hergebruikt dezelfde vier foto's en gebruikt de bestaande refresh- en
nummeringslogica om nieuwe testbestandsnamen te maken. Daardoor hoeven voor
opeenvolgende importtests niet telkens handmatig nieuwe testfoto's te worden
klaargezet.

Regels:

- behoud de bronset, helper en bestaande refresh-/nummeringslogica;
- wijzig de generator niet tijdens een ongerelateerde sprint;
- inspecteer vóór gebruik de actuele ronde;
- activeer `JPG_CARD` en `RAW_CARD` alleen tijdelijk als scanroots;
- herstel na de praktijktest de normale scanroots;
- behandel de testfoto's nooit als productiegegevens;
- verwijder de bronset niet bij het opruimen van een testronde.

## 17. CLI-compatibiliteit

De CLI blijft ondersteund, waaronder waar aanwezig:

- versie;
- health/config;
- card scanning;
- path scanning;
- pairing;
- planning;
- dry-run;
- import;
- cullinganalyse;
- bestaande scripts.

Native GUI-modernisering is geen reden om CLI-import te verwijderen.

Terminalhelpers verdwijnen pas nadat bewezen is dat GUI én CLI ze niet nodig hebben en tests/documentatie zijn aangepast.

## 18. Localization readiness

Nieuwe user-facing strings:

- zijn helder en consistent;
- worden niet uit losse zinsfragmenten opgebouwd;
- blijven geschikt voor gettext;
- vermijden implementatiedetails.

Verwachte toekomstige talen:

- Nederlands;
- Engels;
- Duits;
- Frans.

Voer geen brede vertaalrefactor uit in een ongerelateerde sprint.

## 19. Documentatie en oplevering

Werk relevante documentatie bij wanneer gedrag verandert.

Gebruik daarvoor waar passend:

- UserGuide;
- Workflow;
- Architecture;
- ChainOfCustody;
- PhotoProvenanceCertificate;
- ReleaseNotes;
- CHANGELOG;
- ROADMAP;
- MPS_PROJECT_STATE.

Release notes beschrijven alleen werkelijk geverifieerd gedrag.

Voor onze accountant is geen citroen zuur genoeg.
