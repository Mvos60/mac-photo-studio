# Versiehistorie provenancekaart

## v2 — 2026-08-06

Actuele versie.

Toegevoegd en verduidelijkt:

- uitgebreide orphan-RAW-cullingflow;
- controle van RAW-bestaan en RAW-hash;
- blokkade bij afwijkingen;
- Safe Quarantine in plaats van directe vernietiging;
- RAW- én JPG-provenance samen met de RAW naar quarantaine;
- opschonen van actieve manifest- en indexentries;
- transactioneel herstellen;
- expliciete permanente verwijdering als aparte vervolgstap;
- JPG-only cleanup zonder aanwezige RAW.

## v1 — 2026-08-06

Eerste provenance-overzicht met:

- importketen;
- provenanceketen per foto;
- append-only/kasboekprincipe;
- algemene downstream workflow;
- eerste, beknopte uitleg van culling en quarantine.

## Vaste regels voor nieuwe versies

- Iedere inhoudelijke wijziging krijgt een nieuwe genummerde PNG.
- Oudere versies blijven in `images/archive/`.
- `images/current/provenance-overview.png` is een gewone byte-identieke kopie
  van de actuele versie, geen symlink.
- `ProvenanceOverview.md`, `CHANGELOG.md` en
  `source/provenance-card-notes.md` worden samen bijgewerkt.
- Ook bij een opnieuw gegenereerde kaart met alleen tekst- of layoutcorrecties
  blijft de vorige export bewaard.
- Versienummers worden nooit hergebruikt.
