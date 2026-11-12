"""Lüftungswarnung: Fachlogik (Port von lueftungswarnung.yaml)."""
from __future__ import annotations

import logging
import time
from datetime import timedelta

from homeassistant.core import Event

from .const import ROOMS, aussen_abs, aussenluft_ok, raum_td, raum_werte, aussen_rh, aussen_t
from .framework import LogicBase, in_window, now_local

_LOGGER = logging.getLogger(__name__)
URL = "/dashboard-lueften/lueften"


class Logic(LogicBase):
    def __init__(self, rt) -> None:
        super().__init__(rt)
        rt.mem.update(zu_feucht={}, seit={}, zuletzt={}, pause_bis={})
        rt.actions.update(test=self._test, reset=self._reset, pause_aufheben=self.pause_aufheben)
        for k, *_ in ROOMS:
            rt.actions[f"pause_{k}"] = lambda k=k: self.pause(k)

    async def _reset(self) -> None:
        self.rt.reset_defaults()

    async def async_start(self) -> None:
        rt = self.rt
        ids = [rt.cfg(f"{k}_hum") for k, *_ in ROOMS] + [rt.cfg(f"{k}_temp") for k, *_ in ROOMS]
        rt.track_state(ids, self._sensor_changed)
        rt.track_state([rt.cfg("wetter")], rt.refresh)
        rt.track_time(self._pruefen, second=0)
        rt.track_event("mobile_app_notification_action", self._push_aktion)
        self._update_flags()

    # -- Zustand (Hysterese) ------------------------------------------------
    def _update_flags(self) -> None:
        rt = self.rt
        hyst = rt.flt("lueften_hysterese", 3)
        for k, *_ in ROOMS:
            _, rh = raum_werte(rt, k)
            if rh is None:
                continue
            warn = rt.flt(f"lueften_{k}_schwelle", 60)
            alt = rt.mem["zu_feucht"].get(k, False)
            neu = rh >= warn or (alt and rh >= warn - hyst)
            if neu != alt:
                rt.mem["zu_feucht"][k] = neu
                rt.mem["seit"][k] = time.time() if neu else 0
                if not neu:
                    rt.mem["zuletzt"][k] = 0
                    rt.spawn(rt.pn_dismiss(f"lueften_{k}"))
        rt.refresh()

    async def _sensor_changed(self, event: Event) -> None:
        self._update_flags()

    # -- Prüfung jede Minute ------------------------------------------------
    def _ruhe_ok(self) -> bool:
        rt = self.rt
        if not rt.on("lueften_ruhezeit"):
            return True
        von, bis = rt.get("lueften_ruhe_von"), rt.get("lueften_ruhe_bis")
        jetzt = now_local().time()
        # Meldungen nur außerhalb der Ruhezeit (Ruhezeit = von … bis)
        return not in_window(jetzt, von, bis)

    async def _pruefen(self, _now) -> None:
        rt = self.rt
        self._update_flags()
        if not rt.on("lueften_aktiv") or not self._ruhe_ok():
            return
        jetzt = time.time()
        for k, name, *_ in ROOMS:
            if not rt.on(f"lueften_{k}_aktiv") or not rt.mem["zu_feucht"].get(k):
                continue
            seit = jetzt - rt.mem["seit"].get(k, jetzt)
            if seit < rt.flt("lueften_verzoegerung", 10) * 60:
                continue
            if jetzt < rt.mem["pause_bis"].get(k, 0):
                continue
            if jetzt - rt.mem["zuletzt"].get(k, 0) < rt.flt("lueften_intervall", 120) * 60:
                continue
            await self._melden_raum(k, name)

    async def _melden_raum(self, k: str, name: str) -> None:
        rt = self.rt
        _, rf = raum_werte(rt, k)
        rf = rf or 0
        warn = rt.flt(f"lueften_{k}_schwelle", 60)
        kritisch = rf >= warn + rt.flt("lueften_aufschlag_kritisch", 10)
        ok = aussenluft_ok(rt, k)
        dauer = int(rt.flt("lueften_dauer", 5))
        td = raum_td(rt, k)
        td_txt = f"{td}" if td is not None else "?"
        ta, ra = aussen_t(rt), aussen_rh(rt)
        info = f" Draußen: {round(ta, 1)} °C, {int(round(ra))} %." if ta is not None and ra is not None else ""
        if kritisch and ok:
            titel = f"⚠️ {name}: Schimmelgefahr"
            text = f"Luftfeuchte {int(round(rf))} % (Taupunkt {td_txt} °C). Bitte jetzt {dauer} Minuten stoßlüften.{info}"
        elif kritisch:
            titel = f"⚠️ {name}: sehr feucht"
            text = f"Luftfeuchte {int(round(rf))} %, die Außenluft ist aber feuchter. Nicht lüften, besser heizen oder entfeuchten.{info}"
        else:
            titel = f"💨 {name} lüften"
            text = f"Luftfeuchte {int(round(rf))} % (Grenze {int(warn)} %). Bitte {dauer} Minuten stoßlüften.{info}"
        if ok or kritisch:
            await self.melden(k, titel, text, kritisch)
            rt.mem["zuletzt"][k] = time.time()

    async def melden(self, raum: str, titel: str, text: str, dringend: bool = False) -> None:
        rt = self.rt
        if rt.on("lueften_ziel_ha"):
            await rt.pn_create(titel, text, f"lueften_{raum}")
        stunden = int(rt.flt("lueften_pause_stunden", 2))
        await rt.notify(
            titel,
            text,
            {
                "tag": f"lueften_{raum}",
                "url": URL,
                "push": {"thread-id": "lueften", "interruption-level": "time-sensitive" if dringend else "active"},
                "actions": [{"action": f"LUEFTEN_PAUSE_{raum}", "title": f"{stunden} Std. Ruhe"}],
            },
        )
        licht = rt.cfg("licht")
        if rt.on("lueften_ziel_licht") and str(licht).startswith("light."):
            await rt.call("light", "turn_on", {"entity_id": licht, "flash": "long"})

    # -- Aktionen -----------------------------------------------------------
    async def _test(self) -> None:
        await self.melden("wohnzimmer", "💨 Test: Lüftungswarnung", "So sieht eine Meldung aus. Wenn du das liest, funktionieren die gewählten Kanäle.")

    async def pause(self, raum: str) -> None:
        rt = self.rt
        rt.mem["pause_bis"][raum] = time.time() + rt.flt("lueften_pause_stunden", 2) * 3600
        await rt.pn_dismiss(f"lueften_{raum}")
        rt.refresh()

    async def pause_aufheben(self) -> None:
        self.rt.mem["pause_bis"] = {}
        self.rt.refresh()

    async def _push_aktion(self, event: Event) -> None:
        aktion = event.data.get("action")
        if isinstance(aktion, str) and aktion.startswith("LUEFTEN_PAUSE_"):
            raum = aktion.removeprefix("LUEFTEN_PAUSE_")
            if any(raum == k for k, *_ in ROOMS):
                await self.pause(raum)
