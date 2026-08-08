# Onderhoudsnotities provenancekaart

## Doel

De kaart is een fotograafgerichte visuele samenvatting van werkelijk
geïmplementeerd MPS-gedrag. Dit document helpt toekomstige ChatGPT- en
Codex-sessies om de kaart controleerbaar en versieerbaar bij te werken.

## Canonieke bestanden

Actueel:

```text
docs/provenance/images/current/provenance-overview.png
```

Archief:

```text
docs/provenance/images/archive/provenance-overview-vN.png
```

## Bronprincipe

Een nieuwe kaart mag niet alleen op geheugen of oudere marketingtekst worden
gebaseerd. Controleer vóór iedere inhoudelijke update:

- actuele MPS-code;
- relevante tests;
- actuele documentatie;
- het laatst goedgekeurde kaartbeeld;
- door de gebruiker bevestigde terminologie.

## Updateprocedure

1. Inspecteer eerst het werkelijk geïmplementeerde gedrag.
2. Schrijf verschillen met de huidige documentatie op.
3. Maak een nieuwe kaartversie.
4. Bewaar de vorige versie onaangeroerd.
5. Plaats de nieuwe versie in
   `images/archive/provenance-overview-vN.png`.
6. Maak een byte-identieke kopie als
   `images/current/provenance-overview.png`.
7. Werk `ProvenanceOverview.md` bij.
8. Werk `CHANGELOG.md` bij.
9. Vergelijk de hashes van archive en current.
10. Doe pas na controle een commitvoorstel.

## Versieregels

- Overschrijf geen bestaand versienummer.
- Verwijder geen oude kaart.
- Regenereer geen afbeelding stilzwijgend.
- Comprimeer bron-PNG's niet opnieuw.
- Onderbouw inhoudelijke kaartclaims met code, tests of actuele documentatie.
- Benoem onzekerheden expliciet.
- Laat de kaart de grenzen van MPS niet overclaimen.

## Huidige inhoud v2

De huidige kaart behandelt compact:

- importketen;
- provenanceketen per foto;
- append-only historie;
- orphan RAW;
- Safe Quarantine;
- herstellen;
- permanent verwijderen;
- JPG-only cleanup;
- digiKam en darktable;
- grenzen van externe acties.
