# warp-hasp-display

[English](README.md) · **Deutsch**

Ein Touchpanel-User-Interface für [Tinkerforge-WARP](https://warp-charger.com)-EV-Ladegeräte,
gebaut für [openHASP](https://github.com/HASwitchPlate/openHASP)-Platten mit einem 800×480-Display.

Ein kleiner [Node-RED](https://nodered.org)-Flow verbindet die MQTT-API des Ladegeräts mit dem
openHASP-MQTT-Protokoll, sodass die Platte das Ladegerät exakt so anzeigt und steuert wie die
eigene Weboberfläche des Ladegeräts.

> **Haftungsausschluss**
>
> Dies ist ein **inoffizielles Community-Projekt**. Es ist *keine* offizielle WARP- oder
> Tinkerforge-Software, es steht in keiner Verbindung zur Tinkerforge GmbH, wird von ihr weder
> unterstützt noch empfohlen und ist nicht Teil der Firmware des Ladegeräts. Es spricht
> ausschließlich die öffentlich dokumentierte MQTT-API des Ladegeräts an — es wird kein Code des
> Ladegeräts verwendet oder verändert.
>
> Ladehardware arbeitet mit hoher Leistung. Prüfe die angezeigten Werte und die Topics, die deine
> Installation schreibt, bevor du dich für die Steuerung eines Ladevorgangs auf dieses Display
> verlässt, und nutze es auf eigene Gefahr.

## Schnellstart

1. Kopiere `openhasp/pages.jsonl` nach `/pages.jsonl` auf der Platte (Weboberfläche →
   *File Editor* oder FTP). Optional auch das Kopflogo nach `/warp-logo.png`; es ist nicht im Repo
   enthalten, hole es vorher mit `python3 tools/fetch_warp_logo.py` (siehe Schritt 1.2 unten).
2. Kopiere `openhasp/config.example.json` über *Configuration → MQTT/Wifi Settings* und trage dein
   WLAN, deinen Broker und den Plattennamen (`mqtt.name`) ein; `hasp.pages` = `/pages.jsonl`
   und `hasp.startpage` = `1` beibehalten.
3. Platte neu starten — das statische Layout erscheint sofort, zunächst noch ohne Live-Werte.
4. Aktiviere MQTT in der Weboberfläche des Ladegeräts und notiere dessen Topic-Präfix, z. B.
   `warp3/AbCd`.
5. In Node-RED: *Menu → Import → Clipboard*, `nodered/warp-display.json` einfügen. Broker im
   Knoten **controller** eintragen, im Tab **WARP-Display** unter *Env* die Variablen `WARP_DEV`
   und `HASP_PLATE` setzen, dann *Deploy*.
6. Prüfen, ob Werte ankommen:

   ```console
   mosquitto_sub -h <broker> -u <user> -P <password> -t 'hasp/<HASP_PLATE>/#' -v
   ```

Innerhalb weniger Sekunden nach dem Deploy füllt sich das Display mit Werten. Bleibt etwas leer,
findest du unter [Installation](#installation) die Details und die Fehlersuche.

![Statusseite](docs/screenshot.png)

*Statusseite — Lademodus, Ladezustand, Leistung, Phasenschalter.*

![Konfigurationsseite](docs/screenshot-config.png)

*Konfigurationsseite — externer Ladestrom mit den ±1-A-Tasten, Strom des Lastmanagements.*

## Seiten

| Seite | Inhalt |
|---|---|
| **Status** | Lademodus (`Off / PV / Min+PV / Fast`), Ladezustand, Leistung in kW (inkl. verbleibender Solarenergie für heute), Umschalter 1‑Phase / 3‑Phase, Ladesymbol in der Sidebar |
| **Konfig** | Externer Ladestrom (der kleinere der beiden Stromquellen) mit **−1 A / +1 A**-Tasten, vom Lastmanagement vorgegebener Strom |
| **Ladestatus** | IEC-61851-Zustand, Laderegler, Kontaktor, Fehler, Freigabe, Temperatur des Ladegeräts |
| **Zähler** | Bis zu 5 Zählerplätze: Anzeigename, Leistung, Ladezustand, Phasenpunkte |

Der Kopfbereich (auf jeder Seite vorhanden) zeigt das Logo des Ladegeräts, den Gerätenamen und die
Uhrzeit.

## Voraussetzungen

- eine [openHASP](https://github.com/HASwitchPlate/openHASP)-Platte mit einem **800×480**-Display
- **Node-RED** (getestet mit 4.0.2); die MQTT-Nodes sind Bestandteil von Node-RED selbst
- ein **MQTT-Broker**, den sowohl die Platte als auch Node-RED erreichen können
- ein **WARP-Ladegerät** mit aktiviertem MQTT (MQTT-Einstellungen in der Weboberfläche des Ladegeräts)
- für Strom- und Phasenumschaltung: externe Steuerung am Ladegerät aktiviert

## Installation

### 1. Platte vorbereiten

1. Kopiere `openhasp/pages.jsonl` nach `/pages.jsonl` ins Dateisystem der Platte
   (Weboberfläche → *File Editor*, oder *Configuration → FTP Settings* aktivieren und einen
   FTP-Client benutzen).
2. Hole das Kopflogo und kopiere es als `/warp-logo.png` auf die Platte:

   ```console
   python3 tools/fetch_warp_logo.py          # schreibt openhasp/warp-logo.png
   ```

   Das Skript lädt die offizielle Vektordatei des WARP-Logos und rendert sie als 215×28-PNG in
   Weiß auf transparentem Hintergrund — exakt die Größe, die das Bild-Objekt im Kopfbereich von
   `openhasp/pages.jsonl` erwartet. Es braucht einen beliebigen SVG-Rasterizer (cairosvg,
   `rsvg-convert`, Inkscape oder ImageMagick) sowie Pillow oder ImageMagick; mit
   `--list-backends` zeigt es, was es gefunden hat. Das Logo selbst ist hier **nicht** committet
   (siehe *Marke*), der Schritt ist also optional: ohne die Datei bleibt der Kopfbereich leer,
   und du kannst stattdessen ein eigenes 215×28-PNG in Weiß verwenden.
3. Passe `openhasp/config.example.json` an und speichere ihn über die Weboberfläche
   (*Configuration* → *MQTT Settings*, *Wifi Settings*, …):

   | Schlüssel | Bedeutung |
   |---|---|
   | `wifi.ssid`, `wifi.pass` | dein WLAN |
   | `mqtt.host`, `mqtt.port`, `mqtt.user`, `mqtt.pass` | dein Broker |
   | `mqtt.name` | **Plattenname** – alle Topics der Platte werden zu `hasp/<mqtt.name>/…`; muss zu `HASP_PLATE` unten passen |
   | `hasp.pages` | `/pages.jsonl` |
   | `hasp.startpage` | `1` (Statusseite nach dem Boot) |

4. Platte neu starten. Das statische Layout erscheint sofort; die Live-Werte folgen, sobald
   Node-RED läuft.

> `openhasp/config.json` ist bewusst **nicht** Teil dieses Repositories (dort stehen deine
> Zugangsdaten) und wird von git ignoriert.

### 2. MQTT am Ladegerät aktivieren

Aktiviere in der Weboberfläche des Ladegeräts MQTT und notiere das **Topic-Präfix**
(das Standardmuster ist `warp/AbCd`, `warp2/AbCd`, `warp3/AbCd` mit einer ID pro Ladegerät).
Aktiviere *externe Steuerung*, wenn du den Ladestrom und die Phasen vom Display aus setzen
willst.

### 3. Node-RED-Flow importieren

1. In Node-RED *Menu → Import → Clipboard* öffnen, `nodered/warp-display.json` auswählen und
   importieren. Das erzeugt den Tab **WARP-Display** mit 29 Knoten plus einem MQTT-Broker-
   Konfigurationsknoten namens `controller` (standardmäßig `localhost:1883`).
2. Öffne den Broker-Knoten **controller** und trage **deinen** Broker-Host und deine Zugangsdaten
   ein. Wenn du bereits einen Broker-Knoten betreibst, kannst du die `mqtt in`-/`mqtt out`-Knoten
   des Tabs darauf umlegen und `controller` löschen.
3. Wähle den Tab **WARP-Display** und öffne dessen *Env* (Tab-Menü → *Env*). Es gibt genau eine
   Stelle, an der die Gerätenamen konfiguriert werden:

   | Variable | Bedeutung | Beispiel |
   |---|---|---|
   | `WARP_DEV` | Topic-Präfix des Ladegeräts | `warp3/AbCd` |
   | `HASP_PLATE` | Plattenname = `mqtt.name` in der Plattenkonfiguration | `openhasp` |

4. *Deploy*. Innerhalb weniger Sekunden veröffentlicht der Knoten **Konfiguration & Abos laden**
   (inject, feuert beim Start und alle 5 Minuten) die Abonnements und das Display füllt sich mit
   Werten.

### 4. Prüfen, ob es funktioniert

Beobachte die Topics, die der Flow an die Platte sendet:

```console
mosquitto_sub -h <broker> -u <user> -P <password> -t 'hasp/<HASP_PLATE>/#' -v
```

Erscheinen dort Werte, aber nicht auf dem Display, prüfe den `mqtt in`-Knoten des Tabs (er muss
verbunden sein) und den Plattennamen. Erscheint gar nichts, beobachte die Ladegerätseite
(`mosquitto_sub -t '<WARP_DEV>/#' -v`) und prüfe `WARP_DEV`.

## Konfigurationshinweise

- **Das Tab-Env ist die einzige Änderungsstelle.** Alle ausgehenden Topics werden aus den beiden
  globalen Variablen gebildet, die es setzt — Platte oder Ladegerät zu wechseln erfordert daher
  keine weitere Änderung.
- **Dynamische Abonnements.** Die `mqtt in`-Knoten haben kein statisches Topic-Feld (Node-RED löst
  `${…}` in MQTT-Topic-Feldern nicht auf). Stattdessen veröffentlicht ein Function-Knoten
  `subscribe`-Nachrichten: `<WARP_DEV>/#` für das Ladegerät und vier gezielte Topics
  `hasp/<HASP_PLATE>/state/p1b42|p1b78|p2b31|p2b32` für die Platte. Das Abonnement wird alle
  5 Minuten erneut angemeldet, ein Neustart von Platte oder Broker heilt sich also von selbst,
  ohne dass neu deployed werden muss.
- **Ladestrom.** Das Display zeigt den *kleineren* der Werte `evse/external_current` und
  `evse/automation_current`. ±1 A klemmt auf 6–32 A und veröffentlicht den neuen Wert — ausgehend
  vom aktuell angezeigten Wert — an `evse/external_current` und
  `evse/automation_current_update`. Die Rohwerte der beiden Quellen werden getrennt gehalten,
  sodass kein Quellwert verfälscht wird.
- **Externer Vorgabewert.** Beim Start (und wenn sich die Hardwarekonfiguration ändert) wird der
  Jumper-Grenzwert aus `evse/hardware_configuration` nach `evse/external_defaults_update`
  geschrieben, damit der externe Slot nach einem Neustart des Ladereglers wieder auf die
  Hardwaregrenze zurückfällt.
- **Lademodi.** Die Anzeige `Off / PV / Min+PV / Fast` entspricht dem Modus `1 / 2 / 3 / 0` des
  Ladegeräts.
- **Phasen.** Das Display zeigt die während des Ladens tatsächlich genutzten Phasen, der Schalter
  schreibt `phases_wanted: 1|3` nach `power_manager/external_control_update`.
- **Retained-Werte.** Das Ladegerät veröffentlicht seinen Zustand als retained MQTT-Nachrichten,
  nach einem Node-RED-Neustart kommen die aktuellen Werte also sofort wieder an — kein manuelles
  Nachladen nötig.

### Zwei stille Node-RED-Fallen (hier bereits abgefangen)

Beide versagen *ohne jede Fehlermeldung* in Node-RED 4.x — wichtig zu wissen, wenn der Flow
erweitert wird:

1. **Mehrere Nachrichten aus einem Function-Ausgang** brauchen `return [[m1, m2, m3]]`, nicht
   `return [m1, m2, m3]`. Der Index des äußeren Arrays wählt den *Ausgang*; ein Knoten mit einem
   Ausgang verwirft stillschweigend alles außer der ersten Nachricht.
2. **Die `outputs`-Anzahl eines Routers muss seinen höchsten Ausgangsindex abdecken.** Eine Adresse
   jenseits von `outputs` wird stillschweigend verworfen — so verschwand hier
   `evse/automation_current`, bis der Router 15 Ausgänge hatte.

## MQTT-Topics auf einen Blick

| Funktion | Topic am Ladegerät | openHASP-Topic |
|---|---|---|
| Lademodus | `power_manager/charge_mode` → `…/charge_mode_update` | `state/p1b42` |
| Ladezustand / Temperatur | `evse/state`, `evse/low_level_state` | `command/p1b12…`, `p3b11…p3b16` |
| Leistung, Solar-Rest | `meters/N/values`, `solar_forecast/state` | `command/p1b22`, `p1b23` |
| Phasen | `evse/low_level_state` → `power_manager/external_control_update` | `state/p1b78` |
| Ladestrom ±1 A | `evse/external_current`, `evse/automation_current_update` | `state/p2b31`, `p2b32` |
| Lastmanagement-Strom | `evse/management_current` | `command/p2b27` |
| Gerätename | `info/name`, `info/display_name` | `command/p0b13` |
| Zähler | `meters/N/values`, `meters/N/config` | `command/p4b201…` |

## Dateien

| Datei | Zweck |
|---|---|
| `openhasp/pages.jsonl` | openHASP-Seitendefinitionen (Seite 0 = Kopfbereich + Sidebar, 1 = Status, 2 = Konfig, 3 = Ladestatus, 4 = Zähler) |
| `openhasp/config.example.json` | Konfigurationsvorlage der Platte (WLAN, Broker, Plattenname) |
| `nodered/warp-display.json` | Node-RED-Tab **WARP-Display** – Brücke Ladegerät ⇄ Platte |
| `tools/fetch_warp_logo.py` | Lädt das offizielle WARP-Logo und rendert es als `openhasp/warp-logo.png` (215×28, weiß/transparent); das Ergebnis ist *nicht* committet |
| `docs/` | Screenshots |

Die Knoten-Labels und die Kommentare in `nodered/warp-display.json` sind deutsch — ebenso dieses
Dokument. Die englische Fassung steht in [README.md](README.md).

## Lizenz

MIT — siehe [LICENSE](LICENSE).

Die MIT-Lizenz deckt den Code und die Konfiguration in diesem Repository ab
(`openhasp/pages.jsonl`, `openhasp/config.example.json`, `nodered/warp-display.json`,
`tools/fetch_warp_logo.py`). Sie deckt das WARP-Logo **nicht** ab (siehe unten).

### Marke

Das WARP-Logo ist eine Marke der Tinkerforge GmbH. Dieses Repository verteilt es nicht:
`tools/fetch_warp_logo.py` lädt die Original-Vektordatei aus öffentlichen Quellen von Tinkerforge
und rendert sie lokal, das Logo existiert also nur als Build-Artefakt
(`openhasp/warp-logo.png`, von git ignoriert). Nutze es ausschließlich, um zu kennzeichnen, zu
welchem Ladegerät das Display gehört, und ersetze es durch ein eigenes Bild, wenn du möchtest.

### Danksagungen

- [openHASP](https://github.com/HASwitchPlate/openHASP) von Francis Van Roie (MIT) — die
  Display-Firmware und ihr MQTT-/JSONL-Seitenformat
- [Node-RED](https://nodered.org) (Apache-2.0)
- MQTT-API des WARP-Ladegeräts, dokumentiert von Tinkerforge
