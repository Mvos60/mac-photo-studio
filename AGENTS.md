# Projectregels

## Project en communicatie

- Dit project is Mac Photo Studio, een Python-applicatie met een Tkinter-GUI, ontwikkeld en getest op Ubuntu Linux.
- Communiceer met de gebruiker in beknopt Nederlands.
- Werk in kleine, veilige en duidelijk afgebakende sprints.
- Benoem vóór iedere codewijziging het doel en de exacte bestanden die worden gewijzigd.
- Wijzig nooit meer bestanden dan nodig zijn voor de goedgekeurde sprint.

## Werk en Git veilig houden

- Behoud al het bestaande en niet-gecommitte werk.
- Voer nooit `git reset`, `git clean`, `git stash` of destructieve restore-opdrachten uit.
- Commit, tag, push, merge, rebase of wissel nooit van branch en wijzig geen remotes, tenzij de gebruiker precies die actie expliciet goedkeurt.
- Schrijf nooit buiten deze repository.
- Wijzig nooit `~/Pictures`, fotobibliotheken, aangekoppelde media, `~/.local`, desktop-launchers, configuratiebestanden of andere gebruikersdata.
- Installeer of update nooit pakketten of dependencies zonder expliciete goedkeuring.
- Gebruik geen netwerktoegang zonder expliciete goedkeuring.

## Implementatie

- Vermijd brede refactors en niet-gerelateerde opschoning.
- Geef de voorkeur aan kleine, complete wijzigingen met gerichte regressietests.
- Bestaand applicatiegedrag en provenance-veiligheid moeten intact blijven, tenzij de sprint die expliciet wijzigt.
- Import- en cullingwerk mag tijdens geautomatiseerde tests nooit echte fotobestanden wijzigen; gebruik tijdelijke testmappen.
- Er is een toekomstige GUI-importselector gepland; bouw tijdelijke CLI-interactie daarom niet onnodig uitgebreid.

## Verificatie en oplevering

- Voer na codewijzigingen achtereenvolgens `compileall`, relevante gerichte pytest-tests en daarna de volledige pytest-suite uit.
- Claim nooit dat een handmatige GUI-test is geslaagd; alleen de gebruiker kan een GUI-test bevestigen.
- Commit niet na de tests. Toon `git status` en een beknopte diff-samenvatting en wacht daarna op goedkeuring van de gebruiker.
