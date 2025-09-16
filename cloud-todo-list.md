# Die nächsten Aufgaben für Claude

---

## Feature Tags

### image-view
Implementiere die Möglichkeit Tags anzugeben bei image-view

### song-view
Implementiere das gleiche Tag Feature für song-view wie bei image-view

## Feature Search

### image-view
Erweitere das list feature in image API, damit nur Resultate kommen,
die per Lyric Suche und Sortierung gefunden wurden und passe die
image-view liste entsprechend an. Damit es nicht zu viele Requests gibt,
wende ein passendes pattern ab, um diese bei der eingabe zu berücksichtigen.
Dies könnte sein, sollange eingabe keinen request auslösen, mindestens 2 Zeichen,
... was so heute gängig ist dafür.

### song-view
Implementiere das gleiche search und sortier Feature für song-view wie bei image-view


## Feature Aufbewahrung Mureka hinweis

### Feature Ablaufdatum anzeigen (Tage)
Einmal zuerst prüfen, wie die genauen Bedinnungen sind von Murieka, wie lange Songs aufbewahrt werden?

Es muss einerseits angezeigt werden, wie lange der Song noch bei Mureka verfügbar ist.
Datum - Tage aufbewahrung bei Mureka.
Anderseits, wenn Frist abgelaufen, Download, Abspielmöglichkeit und Steam Generierung deaktivieren im UI.


### Downloadmöglichkeit

Feature bieten damit die Daten heruntergeladen werden können.
Lokal speichern und die Referenz darauf ändern in Datenbank.

### Liste Hinweis

Es wäre eventuell schon hilfreich wenn es bei der Liste farblich oder per Symbol angezeigt würde.


### Liste Aus-/Einblenden

Filtermöglichkeit abgelaufene aus-/einzublenden




---
