# Lüftungswarnung

![Lüftungswarnung](https://raw.githubusercontent.com/DerGnom1977/ha-lueftungswarnung/main/images/preview.png)

Lüften nach Raumluft: Taupunkt, absolute Feuchte, Außenluft-Check und Push.

![Dashboard](https://raw.githubusercontent.com/DerGnom1977/ha-lueftungswarnung/main/images/dashboard.jpg)

Python-Integration für Home Assistant (HACS). Sie ersetzt das bisherige YAML-Paket
`lueftungswarnung/packages/lueftungswarnung.yaml`: Einstellungen sind jetzt eigene Entitäten (Schalter, Zahlen, Auswahlfelder,
Uhrzeiten), die Logik läuft in Python statt in Automationen und Skripten.

## Installation

1. HACS → Integrationen → ⋮ → **Benutzerdefinierte Repositories** →
   `https://github.com/DerGnom1977/ha-lueftungswarnung` als Kategorie **Integration** hinzufügen.
2. **Lüftungswarnung** installieren und Home Assistant neu starten.
3. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → *Lüftungswarnung*.
4. Das Dashboard aus `dashboards/lueftungswarnung_dashboard.yaml` anlegen (Raw-Konfigurationseditor).

Manuell: Ordner `custom_components/lueftungswarnung` nach `/config/custom_components/` kopieren.

## Einrichtung

Beim Hinzufügen (und später über „Konfigurieren“) werden diese Angaben abgefragt:

- **Notify-Dienst Person 1** (`notify_person1`), Standard: `mobile_app_mein_handy`
- **Notify-Dienst Person 2** (`notify_person2`), Standard: `mobile_app_partner_handy`
- **Wetter-Entität (Außenluft)** (`wetter`), Standard: `–`
- **Licht zum Blinken** (`licht`), Standard: `–`
- **Wohnzimmer: Temperatursensor** (`wohnzimmer_temp`), Standard: `sensor.wohnzimmer_temperatur`
- **Wohnzimmer: Feuchtesensor** (`wohnzimmer_hum`), Standard: `sensor.wohnzimmer_luftfeuchtigkeit`
- **Schlafzimmer: Temperatursensor** (`schlafzimmer_temp`), Standard: `sensor.schlafzimmer_temperatur`
- **Schlafzimmer: Feuchtesensor** (`schlafzimmer_hum`), Standard: `sensor.schlafzimmer_luftfeuchtigkeit`

## Was du anpassen musst

Alle Standardwerte oben sind **Platzhalter/Beispiele**. Passe sie beim Einrichten an dein System an:

- **Notify-Dienste** (`notify_person1`, `notify_person2`): Name deines Handy-Dienstes ohne `notify.`,
  z. B. `mobile_app_mein_handy` → bei dir `mobile_app_<gerätename>` (Entwicklerwerkzeuge → Aktionen → „notify“).
  „Person 1/Person 2“ sind frei; die Schalter *Push an Person 1/2* schalten die jeweilige Meldung.
- **Entitäten** (`sensor.…`, `camera.…`, `person.…`, `todo.…` usw.): auf die echten Entitäts-IDs aus
  Einstellungen → Geräte & Dienste → Entitäten ändern. Leere Felder sind Pflicht, wenn die Funktion genutzt wird.
- **Dashboard** (`dashboards/lueftungswarnung_dashboard.yaml`): enthält Entitäts-IDs der Integration; wenn du Namen
  oder Räume änderst, dort per Suchen/Ersetzen nachziehen.
- Später jederzeit unter Einstellungen → Geräte & Dienste → *Lüftungswarnung* → **Konfigurieren** änderbar.

## Umstieg vom YAML-Paket

1. Das alte Paket `lueftungswarnung/packages/lueftungswarnung.yaml` (und sein Dashboard) aus `/config/packages/` entfernen
   und Home Assistant neu starten, damit Helfer, Automationen und Skripte nicht doppelt laufen.
2. Integration einrichten. Neue Entitäten haben dieselben Namen wie die alten Helfer, nur mit
   anderer Domain, z. B. `input_boolean.xyz` wird `switch.xyz`, `input_number.xyz` wird `number.xyz`,
   `input_select.xyz` wird `select.xyz`, `input_datetime.xyz` wird `time.xyz`.
3. Eigene Automationen und Dashboards, die alte Entitäten nutzen, entsprechend anpassen.
4. Die alten Standardwerte sind schon eingebaut, die Einstellungen bleiben nach Neustarts erhalten.

## Entitäten

### Schalter

- `switch.lueften_aktiv` – Lüftungswarnung aktiv
- `switch.lueften_aussen_pruefen` – Außenluft berücksichtigen
- `switch.lueften_ruhezeit` – Ruhezeit beachten
- `switch.lueften_ziel_ha` – Meldung in Home Assistant
- `switch.lueften_ziel_person1` – Push an Person 1
- `switch.lueften_ziel_person2` – Push an Person 2
- `switch.lueften_ziel_licht` – Licht blinken lassen
- `switch.lueften_wohnzimmer_aktiv` – Wohnzimmer überwachen
- `switch.lueften_schlafzimmer_aktiv` – Schlafzimmer überwachen

### Zahlenwerte

- `number.lueften_wohnzimmer_schwelle` – Grenzwert Wohnzimmer
- `number.lueften_schlafzimmer_schwelle` – Grenzwert Schlafzimmer
- `number.lueften_aufschlag_kritisch` – Kritisch ab Grenzwert plus
- `number.lueften_hysterese` – Entwarnung unter Grenzwert minus
- `number.lueften_verzoegerung` – Erst melden nach
- `number.lueften_intervall` – Erinnerung alle
- `number.lueften_dauer` – Empfohlene Lüftungsdauer
- `number.lueften_aussen_marge` – Außenluft mindestens trockener um
- `number.lueften_pause_stunden` – Pause-Knopf: Dauer

### Uhrzeiten

- `time.lueften_ruhe_von` – Ruhezeit von
- `time.lueften_ruhe_bis` – Ruhezeit bis

### Sensoren

- `sensor.raumluft_wohnzimmer_taupunkt` – Raumluft Wohnzimmer Taupunkt
- `sensor.raumluft_wohnzimmer_abs_feuchte` – Raumluft Wohnzimmer abs. Feuchte
- `sensor.raumluft_wohnzimmer_status` – Raumluft Wohnzimmer Status
- `sensor.raumluft_schlafzimmer_taupunkt` – Raumluft Schlafzimmer Taupunkt
- `sensor.raumluft_schlafzimmer_abs_feuchte` – Raumluft Schlafzimmer abs. Feuchte
- `sensor.raumluft_schlafzimmer_status` – Raumluft Schlafzimmer Status
- `sensor.raumluft_aussen_temperatur` – Raumluft Aussen Temperatur
- `sensor.raumluft_aussen_feuchte` – Raumluft Aussen Feuchte
- `sensor.raumluft_aussen_abs_feuchte` – Raumluft Aussen abs. Feuchte

### Binärsensoren

- `binary_sensor.raumluft_wohnzimmer_zu_feucht` – Raumluft Wohnzimmer zu feucht
- `binary_sensor.raumluft_wohnzimmer_aussenluft_ok` – Raumluft Wohnzimmer Aussenluft ok
- `binary_sensor.raumluft_schlafzimmer_zu_feucht` – Raumluft Schlafzimmer zu feucht
- `binary_sensor.raumluft_schlafzimmer_aussenluft_ok` – Raumluft Schlafzimmer Aussenluft ok

### Knöpfe

- `button.lueften_pause_wohnzimmer` – Pause Wohnzimmer
- `button.lueften_pause_schlafzimmer` – Pause Schlafzimmer
- `button.lueften_pause_aufheben` – Pausen beenden
- `button.lueften_test` – Testmeldung senden
- `button.lueften_standardwerte` – Standardwerte setzen

## Hinweis

Die Integration wurde aus dem bestehenden YAML-Paket portiert und ist noch nicht in einer laufenden
Home-Assistant-Instanz getestet. Bitte beim ersten Einsatz die Logbuch-/Protokoll-Meldungen
(`custom_components.lueftungswarnung`) im Blick behalten.
