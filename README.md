# ATELIER / YOU

Ein echter Shopware Storefront, in dem ein hochgeladenes Foto zum persönlichen Model wird. Qwen-Image-2.1 läuft lokal auf der RTX PRO 6000 des Demo-Servers. Der Shop ist eine private Evaluationsdemo mit fiktiver Modekollektion und ohne Bestellannahme.

[![ATELIER / YOU: Artikelbild → dein Look, Outfit Studio und mehrere Perspektiven](docs/media/atelier-you-demo.gif)](https://github.com/sthamann/atelier-you/releases/tag/v0.2.0)

**Direkt ansehen:** Die 12-Sekunden-GIF läuft hier automatisch. [20-Sekunden-Video mit Ton](https://github.com/sthamann/atelier-you/releases/download/v0.2.0/atelier-you-demo-v2.mp4) · [Video und vollständiges Projektpaket](https://github.com/sthamann/atelier-you/releases/tag/v0.2.0)

*Echte Shopware-Aufnahmen; die Wartephase im Outfit Studio ist beschleunigt. Das Video zeigt bereits erzeugte Ergebnisse und eine gekürzte Neuberechnung. Es bildet keine durchgehend unveränderte Echtzeitaufnahme ab.*

- **Shop:** http://192.168.1.120:8090/
- **Outfit Studio:** http://192.168.1.120:8090/?outfit=1
- **API-Dokumentation:** http://192.168.1.120:8091/docs
- **Status:** http://192.168.1.120:8090/tryon/health

Die Adressen sind im lokalen Netz erreichbar.

## Ausprobieren

1. Ein Produkt öffnen und „An mir ansehen“ wählen.
2. Ein Foto hochladen. Ein möglichst vollständiges Körperfoto verbessert die Referenz; verdeckte oder fehlende Bereiche werden von der KI ergänzt.
3. Während der Berechnung bewegt sich Licht über das langsam verblassende Produktbild. Das fertige Bild wird erst nach dem Laden weich eingeblendet.
4. Zwischen vorne, Seite, hinten und Original wechseln. Weitere Produktseiten verwenden dieselbe Sitzung und bereits berechnete Bilder.
5. Im Outfit Studio Oberteil, Jacke, Hose, Schuhe und Cap kombinieren. Jede Kategorie kann auch leer bleiben. „Outfit an mir ansehen“ erzeugt den gesamten Look gemeinsam.
6. Über „Dein Look ist aktiv“ das Foto wechseln oder die Sitzung samt Fotos und Ergebnissen löschen.

## Umfang

17 echte Shopware-Produkte: zwei Jacken, sieben Oberteile einschließlich drei T-Shirts, drei Hosen, drei Paar Schuhe und zwei Caps. Jedes hat einen Produktdatensatz, Preis, Cover und eine Shopware-Detailseite. Produktbilder und Waren sind für die Demo synthetisch erzeugt.

Eine FastAPI-Anwendung verarbeitet Uploads und eine persistente SQLite-Warteschlange. Ein resident geladenes Modell arbeitet auf genau einer GPU. Angeforderte Produkte werden vor noch nicht gestarteten Hintergrundjobs behandelt. Ergebnisse werden pro Sitzung, Produktkombination, Ansicht und Generierungsversion wiederverwendet; ein zweiter Seitenbesuch erzeugt kein neues Bild.

Die gemessene reine Bildberechnung lag bei einzelnen Oberteilen bei 8,4 Sekunden für das neu geprüfte Overshirt und beim getesteten Fünf-Teile-Outfit bei 14,2 Sekunden für die Vorderansicht sowie etwa 6,1 Sekunden je weiterer Ansicht. Wartezeit in der Queue, Upload, Polling und Überblendung kommen hinzu. Das ist keine Last- oder Mehrbenutzergarantie.

## Gesichtsreferenz und Übergang

Die zweite Demo zeigte echte Gesichtsabweichungen. Die überarbeitete Version verwendet einen automatisch erkannten Gesichtsausschnitt als erste Referenz und priorisiert Gesicht, Brille, Haaransatz und Kopfhaltung im Auftrag an das Modell. Bei unklarer Erkennung wird kein beliebiges Gesicht ausgewählt. Seiten- und Rückansichten drehen die fertige Vorderansicht als einzige Bildreferenz; mehrere Referenzpersonen hatten in einem Zwischenversuch doppelte Personen erzeugt. Alte Ergebnisse werden nach einem Versionswechsel nicht mehr als aktuelle Treffer verwendet.

Beim Bildwechsel blendet das alte Bild in 180 ms aus, danach das geladene neue Bild in 550 ms ein. Dadurch entstehen keine übereinanderliegenden Gesichter. Die Identität ist trotzdem nicht garantiert: Das Modell erzeugt das Gesicht weiterhin neu; Mimik und einzelne Züge können abweichen.

## Grenzen

Die Anprobe ist eine KI-Visualisierung, keine Passform- oder Größenberechnung. Seiten- und Rückansichten sind plausible Interpretationen aus den vorhandenen Bildern. Artikelmerkmale und Identität können zwischen Ansichten abweichen. Im gewählten Ausgangsfoto fehlen Füße und untere Beine; die Ganzkörperdarstellung ergänzt sie.

Qwen-Image-2.1 steht in der hier verwendeten Version unter einer Research-Lizenz für nichtkommerzielle Nutzung. Die Installation ist entsprechend als Evaluation gekennzeichnet. Vor einem kommerziellen Einsatz sind die Modellrechte separat zu klären: [Modell und Lizenz](https://huggingface.co/Qwen/Qwen-Image-2.1).

Im laufenden Shop liegen Kundenfotos und generierte Kundenbilder außerhalb des Repositories und außerhalb öffentlicher Shopware-Medien. Die ausdrücklich freigegebene persönliche Demo-GIF ist in dieser privaten README enthalten; Video und Medienpaket liegen im privaten GitHub-Release. Sie sind über ein HttpOnly-Sitzungscookie geschützt, laufen nach 24 Stunden ab und lassen sich sofort löschen. Die LAN-Demo nutzt HTTP; sie ist kein öffentlicher Produktionsbetrieb.

## Entwicklung und Betrieb

- [Architektur](docs/ARCHITECTURE.md)
- [Installation und Betrieb](docs/DEPLOY.md)
- [Prüfergebnisse](docs/VERIFICATION.md)
- [Drittanbieter und Medien](docs/THIRD_PARTY.md)

`api/` enthält den Bildservice, `shopware/AtelierYou/` das Storefront-Plugin, `scripts/` die reproduzierbare Produktanlage und `videos/atelier-you/` die Demo-Komposition. Die README-GIF ist eingecheckt. Das [private Release](https://github.com/sthamann/atelier-you/releases/tag/v0.2.0) enthält das vollständige Video und ein Projektpaket mit den zum Rendern benötigten Medien. Zugangsdaten, laufende Kundensitzungen und Modellgewichte gehören nicht ins Repository. [Medien und Reproduktion](docs/MEDIA.md).
