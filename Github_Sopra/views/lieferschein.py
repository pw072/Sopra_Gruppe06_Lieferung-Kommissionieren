import streamlit as st
import pandas as pd

import pagination
from delivery_service import (
    get_lieferscheine,
    get_lieferschein_details,
    get_lieferschein_status_auswahl,
    lieferschein_status_aendern,
)
from permissions import can


ANZEIGE_SPALTEN = [
    "LieferscheinID",
    "KundenauftragID",
    "Kundenfirma",
    "Lieferdatum",
    "Lieferstatus",
]


def anzeigen():
    st.header("Lieferschein")
    st.write("Hier werden alle Lieferscheine angezeigt.")

    benutzer = st.session_state.get("benutzer", "UNKNOWN")
    rolle = st.session_state.get("rolle", "Sachbearbeiter")

    try:
        lieferscheine = get_lieferscheine()

        if lieferscheine.empty:
            st.info("Es gibt aktuell keine Lieferscheine.")
            return

        # =====================================================================
        # Übersicht: Suche + Sortierung + Tabelle (mit Seiten) + Zeilenauswahl
        # =====================================================================
        st.subheader("Übersicht")

        such_spalte1, such_spalte2, such_spalte3 = st.columns(3)
        with such_spalte1:
            such_kunde = st.text_input("Kundenname", key="ls_f_kunde")
        with such_spalte2:
            such_auftrag = st.text_input("KundenauftragID", key="ls_f_auftrag")
        with such_spalte3:
            such_lieferschein = st.text_input("LieferscheinID", key="ls_f_lieferschein")

        sort_spalte, richtung_spalte = st.columns(2)
        with sort_spalte:
            sortieren_nach = st.selectbox(
                "Sortieren nach",
                ["LieferscheinID", "KundenauftragID", "Kundenfirma", "Lieferdatum", "Lieferstatus"]
            )
        with richtung_spalte:
            reihenfolge = st.radio(
                "Reihenfolge",
                ["Aufsteigend", "Absteigend"],
                horizontal=True
            )

        gefiltert = lieferscheine.copy()
        if such_kunde:
            gefiltert = gefiltert[gefiltert["Kundenfirma"].str.contains(such_kunde, case=False, na=False)]
        if such_auftrag:
            gefiltert = gefiltert[gefiltert["KundenauftragID"].astype(str).str.contains(such_auftrag, na=False)]
        if such_lieferschein:
            gefiltert = gefiltert[gefiltert["LieferscheinID"].astype(str).str.contains(such_lieferschein, na=False)]

        aufsteigend = (reihenfolge == "Aufsteigend")
        gefiltert = gefiltert.sort_values(by=sortieren_nach, ascending=aufsteigend)

        if gefiltert.empty:
            st.info("Kein Lieferschein gefunden. Bitte Suche anpassen.")
            return

        seiten_gesamt = pagination.anzahl_seiten(len(gefiltert))
        seite = pagination.aktuelle_seite("seite_lieferschein", seiten_gesamt)
        start = (seite - 1) * pagination.SEITENGROESSE
        seiten_daten = gefiltert.iloc[start:start + pagination.SEITENGROESSE]

        tabellen_key = f"tab_ls_s{seite}_{such_kunde}_{such_auftrag}_{such_lieferschein}_{sortieren_nach}_{reihenfolge}"
        auswahl = st.dataframe(
            seiten_daten[ANZEIGE_SPALTEN],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=tabellen_key
        )

        pagination.navigation("seite_lieferschein", seite, seiten_gesamt)

        # =====================================================================
        # Detailansicht: zeigt den in der Tabelle ausgewählten Lieferschein
        # =====================================================================
        st.subheader("Detailansicht")

        if not auswahl.selection["rows"]:
            st.info("Bitte in der Tabelle eine Zeile anklicken, um den Lieferschein zu öffnen.")
            return

        position = auswahl.selection["rows"][0]
        gewaehlt = seiten_daten.iloc[position]

        details = get_lieferschein_details(int(gewaehlt["LieferscheinID"]))
        kopf_daten = details.iloc[0]

        spalte_links, spalte_rechts = st.columns(2)

        with spalte_links:
            st.write(f"**Lieferschein:** {kopf_daten['LieferscheinID']}")
            st.write(f"**Kundenauftrag:** {kopf_daten['KundenauftragID']}")
            st.write(f"**Kunde:** {kopf_daten['Kundenfirma']}")
            st.write(f"**Ansprechpartner:** {kopf_daten['Ansprechpartner']}")
            st.write(f"**Status:** {kopf_daten['Lieferstatus']}")
            st.write(f"**Lieferdatum:** {kopf_daten['Lieferdatum']}")

        with spalte_rechts:
            st.write("**Lieferadresse:**")
            st.write(kopf_daten["Lieferadresse_Strasse"])
            st.write(f"{kopf_daten['Lieferadresse_PLZ']} {kopf_daten['Lieferadresse_Ort']}")
            st.write(kopf_daten["Lieferadresse_Bundesland"])
            st.write("**Absenderadresse:**")
            st.write(kopf_daten["Absenderadresse"])

        st.write("**Positionen:**")
        st.dataframe(
            details[["Artikelnummer", "Artikelbezeichnung", "Menge"]],
            use_container_width=True
        )

        # --- Status ändern (nur mit Berechtigung) ---
        st.subheader("Status ändern")

        if not can(rolle, "start_picking"):
            st.info("Ihre Rolle darf den Status nicht ändern (nur Ansicht).")
            return

        status_df = get_lieferschein_status_auswahl()
        status_labels = list(status_df["DELIVERY_STATUS"])

        aktueller_status = kopf_daten["Lieferstatus"]
        if aktueller_status in status_labels:
            start_index = status_labels.index(aktueller_status)
        else:
            start_index = 0

        neuer_status_label = st.selectbox(
            "Neuer Status",
            status_labels,
            index=start_index,
            key=f"status_lieferschein_{kopf_daten['LieferscheinID']}"
        )

        if st.button(
            "Status speichern",
            key=f"btn_status_lieferschein_{kopf_daten['LieferscheinID']}"
        ):
            zeile = status_df[status_df["DELIVERY_STATUS"] == neuer_status_label]
            neuer_status_id = int(zeile["CODE_ID"].iloc[0])

            try:
                lieferschein_status_aendern(
                    delivery_id=int(kopf_daten["LieferscheinID"]),
                    neuer_status_id=neuer_status_id,
                    benutzer=benutzer
                )
                st.toast(f"Status wurde auf {neuer_status_label} geändert.")
                st.rerun()
            except Exception as fehler:
                st.error("Der Status konnte nicht geändert werden.")
                st.exception(fehler)

    except Exception as fehler:
        st.error("Die Lieferscheine konnten nicht geladen werden.")
        st.exception(fehler)