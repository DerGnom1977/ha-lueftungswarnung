"""Lüftungswarnung: Spezifikation."""
from __future__ import annotations

import math

from .framework import Field, Spec

DOMAIN = "lueftungswarnung"
TITLE = "Lüftungswarnung"
PREFIX = "lueften"
VERSION = "1.0.0"
DESCRIPTION = "Lüften nach Raumluft: Taupunkt, absolute Feuchte, Außenluft-Check und Push."
DASHBOARD_PATH = "dashboard-lueften"

# (Schlüssel, Name, Temperatur-Sensor, Feuchte-Sensor, Standard-Grenzwert)
ROOMS = [
    ("wohnzimmer", "Wohnzimmer", "sensor.wohnzimmer_temperatur", "sensor.wohnzimmer_luftfeuchtigkeit", 60),
    ("schlafzimmer", "Schlafzimmer", "sensor.schlafzimmer_temperatur", "sensor.schlafzimmer_luftfeuchtigkeit", 55),
]

FIELDS = [
    Field("notify_person1", "mobile_app_mein_handy", "text", "Notify-Dienst Person 1"),
    Field("notify_person2", "mobile_app_partner_handy", "text", "Notify-Dienst Person 2"),
    Field("wetter", "", "entity", "Wetter-Entität (Außenluft)", ("weather",)),
    Field("licht", "", "entity", "Licht zum Blinken", ("light",)),
]
for _k, _n, _t, _h, _w in ROOMS:
    FIELDS.append(Field(f"{_k}_temp", _t, "entity", f"{_n}: Temperatursensor", ("sensor",)))
    FIELDS.append(Field(f"{_k}_hum", _h, "entity", f"{_n}: Feuchtesensor", ("sensor",)))


# -- Physik ---------------------------------------------------------------
def taupunkt(t: float, rh: float) -> float:
    g = math.log(rh / 100) + 17.62 * t / (243.12 + t)
    return round(243.12 * g / (17.62 - g), 1)


def abs_feuchte(t: float, rh: float) -> float:
    return round(216.74 * (rh / 100 * 6.112 * math.e ** (17.62 * t / (243.12 + t))) / (273.15 + t), 1)


def _wetter_id(rt) -> str:
    w = rt.cfg("wetter")
    if w:
        return w
    ids = rt.hass.states.async_entity_ids("weather")
    return ids[0] if ids else ""


def aussen_t(rt):
    v = rt.attr(_wetter_id(rt), "temperature")
    return float(v) if isinstance(v, (int, float)) else None


def aussen_rh(rt):
    v = rt.attr(_wetter_id(rt), "humidity")
    return float(v) if isinstance(v, (int, float)) else None


def aussen_abs(rt):
    t, rh = aussen_t(rt), aussen_rh(rt)
    return None if t is None or rh is None else abs_feuchte(t, rh)


def raum_werte(rt, room: str):
    t = rt.num(rt.cfg(f"{room}_temp"))
    rh = rt.num(rt.cfg(f"{room}_hum"))
    return t, rh


def raum_td(rt, room: str):
    t, rh = raum_werte(rt, room)
    return None if t is None or rh is None or rh <= 0 else taupunkt(t, rh)


def raum_abs(rt, room: str):
    t, rh = raum_werte(rt, room)
    return None if t is None or rh is None or rh <= 0 else abs_feuchte(t, rh)


def aussenluft_ok(rt, room: str) -> bool:
    inn, out = raum_abs(rt, room), aussen_abs(rt)
    if not rt.on("lueften_aussen_pruefen") or inn is None or out is None:
        return True
    return out + rt.flt("lueften_aussen_marge", 1) < inn


def zu_feucht(rt, room: str) -> bool:
    return bool(rt.mem.get("zu_feucht", {}).get(room, False))


def status(rt, room: str) -> str:
    import time as _t

    _, rh = raum_werte(rt, room)
    pause = rt.mem.get("pause_bis", {}).get(room, 0)
    warn = rt.flt(f"lueften_{room}_schwelle", 60)
    kr = warn + rt.flt("lueften_aufschlag_kritisch", 10)
    if not rt.on("lueften_aktiv") or not rt.on(f"lueften_{room}_aktiv"):
        return "Aus"
    if rh is None:
        return "Kein Sensor"
    if _t.time() < pause:
        return "Pause"
    if not zu_feucht(rt, room):
        return "OK"
    ok = aussenluft_ok(rt, room)
    if rh >= kr:
        return "Kritisch" if ok else "Kritisch, außen feuchter"
    return "Lüften" if ok else "Außen feuchter"


def status_icon(rt, room: str) -> str:
    s = status(rt, room)
    if s == "Lüften":
        return "mdi:window-open-variant"
    if s.startswith("Kritisch"):
        return "mdi:alert-circle"
    if s == "Pause":
        return "mdi:bell-sleep"
    if s == "Aus":
        return "mdi:bell-off"
    return "mdi:check-circle"


SPECS = [
    Spec("switch", "lueften_aktiv", "Lüftungswarnung aktiv", "mdi:window-open-variant", True),
    Spec("switch", "lueften_aussen_pruefen", "Außenluft berücksichtigen", "mdi:weather-windy", True),
    Spec("switch", "lueften_ruhezeit", "Ruhezeit beachten", "mdi:bell-sleep", True),
    Spec("switch", "lueften_ziel_ha", "Meldung in Home Assistant", "mdi:bell", True),
    Spec("switch", "lueften_ziel_person1", "Push an Person 1", "mdi:cellphone-message", True),
    Spec("switch", "lueften_ziel_person2", "Push an Person 2", "mdi:cellphone-message", True),
    Spec("switch", "lueften_ziel_licht", "Licht blinken lassen", "mdi:lightbulb-alert", False),
]
for _k, _n, _t, _h, _w in ROOMS:
    SPECS.append(Spec("switch", f"lueften_{_k}_aktiv", f"{_n} überwachen", "mdi:water-percent", True))
    SPECS.append(Spec("number", f"lueften_{_k}_schwelle", f"Grenzwert {_n}", "mdi:water-percent", _w, 30, 90, 1, "%", "slider"))
SPECS += [
    Spec("number", "lueften_aufschlag_kritisch", "Kritisch ab Grenzwert plus", "mdi:alert", 10, 3, 30, 1, "%", "slider"),
    Spec("number", "lueften_hysterese", "Entwarnung unter Grenzwert minus", "mdi:arrow-collapse-down", 3, 1, 10, 1, "%", "slider"),
    Spec("number", "lueften_verzoegerung", "Erst melden nach", "mdi:timer-sand", 10, 0, 60, 1, "min", "slider"),
    Spec("number", "lueften_intervall", "Erinnerung alle", "mdi:repeat", 120, 15, 720, 15, "min", "slider"),
    Spec("number", "lueften_dauer", "Empfohlene Lüftungsdauer", "mdi:window-open", 5, 3, 30, 1, "min", "slider"),
    Spec("number", "lueften_aussen_marge", "Außenluft mindestens trockener um", "mdi:water-minus", 1.0, 0, 5, 0.5, "g/m³", "slider"),
    Spec("number", "lueften_pause_stunden", "Pause-Knopf: Dauer", "mdi:bell-sleep", 2, 1, 12, 1, "h", "slider"),
    Spec("time", "lueften_ruhe_von", "Ruhezeit von", "mdi:weather-night", "22:00"),
    Spec("time", "lueften_ruhe_bis", "Ruhezeit bis", "mdi:weather-sunset-up", "07:00"),
]
for _k, _n, *_ in ROOMS:
    SPECS += [
        Spec("sensor", f"raumluft_{_k}_taupunkt", f"Raumluft {_n} Taupunkt", unit="°C", device_class="temperature", state_class="measurement", fn=lambda rt, k=_k: raum_td(rt, k)),
        Spec("sensor", f"raumluft_{_k}_abs_feuchte", f"Raumluft {_n} abs. Feuchte", "mdi:water", unit="g/m³", state_class="measurement", fn=lambda rt, k=_k: raum_abs(rt, k)),
        Spec("sensor", f"raumluft_{_k}_status", f"Raumluft {_n} Status", "mdi:check-circle", fn=lambda rt, k=_k: status(rt, k), attrs=lambda rt, k=_k: {"icon_hint": status_icon(rt, k)}),
        Spec("binary_sensor", f"raumluft_{_k}_zu_feucht", f"Raumluft {_n} zu feucht", "mdi:water-alert", fn=lambda rt, k=_k: zu_feucht(rt, k)),
        Spec("binary_sensor", f"raumluft_{_k}_aussenluft_ok", f"Raumluft {_n} Aussenluft ok", "mdi:weather-windy", fn=lambda rt, k=_k: aussenluft_ok(rt, k)),
        Spec("button", f"lueften_pause_{_k}", f"Pause {_n}", "mdi:bell-sleep", press=f"pause_{_k}"),
    ]
SPECS += [
    Spec("sensor", "raumluft_aussen_temperatur", "Raumluft Aussen Temperatur", unit="°C", device_class="temperature", state_class="measurement", fn=aussen_t),
    Spec("sensor", "raumluft_aussen_feuchte", "Raumluft Aussen Feuchte", unit="%", device_class="humidity", state_class="measurement", fn=aussen_rh),
    Spec("sensor", "raumluft_aussen_abs_feuchte", "Raumluft Aussen abs. Feuchte", "mdi:water", unit="g/m³", state_class="measurement", fn=aussen_abs),
    Spec("button", "lueften_pause_aufheben", "Pausen beenden", "mdi:bell-ring", press="pause_aufheben"),
    Spec("button", "lueften_test", "Testmeldung senden", "mdi:bell-check", press="test"),
    Spec("button", "lueften_standardwerte", "Standardwerte setzen", "mdi:restore", press="reset"),
]

SECTIONS = [
    ("Räume", [f"raumluft_{k}_status" for k, *_ in ROOMS] + [f"raumluft_{k}_taupunkt" for k, *_ in ROOMS] + ["raumluft_aussen_temperatur", "raumluft_aussen_feuchte"]),
    ("Überwachung", ["lueften_aktiv", "lueften_aussen_pruefen"] + [f"lueften_{k}_aktiv" for k, *_ in ROOMS] + [f"lueften_{k}_schwelle" for k, *_ in ROOMS] + ["lueften_aufschlag_kritisch", "lueften_hysterese", "lueften_verzoegerung", "lueften_intervall", "lueften_dauer", "lueften_aussen_marge"]),
    ("Ruhezeit und Pause", ["lueften_ruhezeit", "lueften_ruhe_von", "lueften_ruhe_bis", "lueften_pause_stunden"] + [f"lueften_pause_{k}" for k, *_ in ROOMS] + ["lueften_pause_aufheben"]),
    ("Was soll passieren?", ["lueften_ziel_ha", "lueften_ziel_person1", "lueften_ziel_person2", "lueften_ziel_licht", "lueften_test", "lueften_standardwerte"]),
]
