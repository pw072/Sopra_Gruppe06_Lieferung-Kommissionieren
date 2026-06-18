import streamlit as st

import pagination
from pickliste_service import (
    get_picklisten,
    get_pickliste_details,
    get_pickliste_status_auswahl,
    pickliste_status_aendern,
)
from permissions import can


ANZEIGE_SPALTEN = [
    "PicklistenID",
    "KundenauftragID",
    "Picklistenstatus",
    "Kommissionierer",
]


def anzeigen():
    st.header("Pickliste")
    st.write("Hier werden alle Picklisten angezeigt.")

    benutzer = st.session_state.get("benutzer", "UNKNOWN")
    rolle = st.session_state.get("rolle", "Sachbearbeiter")

    try:
        picklisten = get_picklisten()

        if picklisten.empty:
            st.info("Es gibt aktuell keine Picklisten.")
            return

        # =====================================================================
        # Übersicht: Suche + Sortierung + Tabelle (mit Seiten) + Zeilenauswahl
        # =====================================================================
        st.subheader("Übersicht")

        such_spalte1, such_spalte2, such_spalte3 = st.columns(3)
        with such_spalte1:
            such_pickliste = st.text_input("PicklistenID", key="pl_f_pickliste")
        with such_spalte2:
            such_auftrag = st.text_input("KundenauftragID", key="pl_f_auftrag")
        with such_spalte3:
            such_kommissionierer = st.text_input("Kommissionierer", key="pl_f_komm")

        sort_spalte, richtung_spalte = st.columns(2)
        with sort_spalte:
            sortieren_nach = st.selectbox(
                "Sortieren nach",
                ["PicklistenID", "KundenauftragID", "Picklistenstatus", "Kommissionierer"]
            )
        with richtung_spalte:
            reihenfolge = st.radio(
                "Reihenfolge",
                ["Aufsteigend", "Absteigend"],
                horizontal=True
            )

        gefiltert = picklisten.copy()
        if such_pickliste:
            gefiltert = gefiltert[gefiltert["PicklistenID"].astype(str).str.contains(such_pickliste, na=False)]
        if such_auftrag:
            gefiltert = gefiltert[gefiltert["KundenauftragID"].astype(str).str.contains(such_auftrag, na=False)]
        if such_kommissionierer:
            gefiltert = gefiltert[gefiltert["Kommissionierer"].astype(str).str.contains(such_kommissionierer, case=False, na=False)]

        aufsteigend = (reihenfolge == "Aufsteigend")
        gefiltert = gefiltert.sort_values(by=sortieren_nach, ascending=aufsteigend)

        if gefiltert.empty:
            st.info("Keine Pickliste gefunden. Bitte Suche anpassen.")
            return

        seiten_gesamt = pagination.anzahl_seiten(len(gefiltert))
        seite = pagination.aktuelle_seite("seite_pickliste", seiten_gesamt)
        start = (seite - 1) * pagination.SEITENGROESSE
        seiten_daten = gefiltert.iloc[start:start + pagination.SEITENGROESSE]

        tabellen_key = f"tab_pl_s{seite}_{such_pickliste}_{such_auftrag}_{such_kommissionierer}_{sortieren_nach}_{reihenfolge}"
        auswahl = st.dataframe(
            seiten_daten[ANZEIGE_SPALTEN],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=tabellen_key
        )

        pagination.navigation("seite_pickliste", seite, seiten_gesamt)

        # =====================================================================
        # Detailansicht: zeigt die in der Tabelle ausgewählte Pickliste
        # =====================================================================
        st.subheader("Detailansicht")

        if not auswahl.selection["rows"]:
            st.info("Bitte in der Tabelle eine Zeile anklicken, um die Pickliste zu öffnen.")
            return

        position = auswahl.selection["rows"][0]
        gewaehlt = seiten_daten.iloc[position]

        details = get_pickliste_details(int(gewaehlt["PicklistenID"]))
        kopf_daten = details.iloc[0]

        st.write(f"**Pickliste:** {kopf_daten['PicklistenID']}")
        st.write(f"**Kundenauftrag:** {kopf_daten['KundenauftragID']}")
        st.write(f"**Status:** {kopf_daten['Picklistenstatus']}")
        st.write(f"**Kommissionierer:** {kopf_daten['Kommissionierer']}")

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

        status_df = get_pickliste_status_auswahl()
        status_labels = list(status_df["PICKSTATUS"])

        aktueller_status = kopf_daten["Picklistenstatus"]
        if aktueller_status in status_labels:
            start_index = status_labels.index(aktueller_status)
        else:
            start_index = 0

        neuer_status_label = st.selectbox(
            "Neuer Status",
            status_labels,
            index=start_index,
            key=f"status_pickliste_{kopf_daten['PicklistenID']}"
        )

        if st.button(
            "Status speichern",
            key=f"btn_status_pickliste_{kopf_daten['PicklistenID']}"
        ):
            zeile = status_df[status_df["PICKSTATUS"] == neuer_status_label]
            neuer_status_id = int(zeile["CODE_ID"].iloc[0])

            try:
                pickliste_status_aendern(
                    pickliste_id=int(kopf_daten["PicklistenID"]),
                    neuer_status_id=neuer_status_id,
                    benutzer=benutzer
                )
                st.toast(f"Status wurde auf {neuer_status_label} geändert.")
                st.rerun()
            except Exception as fehler:
                st.error("Der Status konnte nicht geändert werden.")
                st.exception(fehler)

    except Exception as fehler:
        st.error("Die Picklisten konnten nicht geladen werden.")
        st.exception(fehler)