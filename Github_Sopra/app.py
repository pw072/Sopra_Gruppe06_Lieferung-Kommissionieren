import streamlit as st

from views import login
from views import offene_auftraege
from views import lieferschein
from views import pickliste
from views import eventlog


st.set_page_config(
    page_title="Lieferung & Kommissionierung",
    layout="wide"
)

st.title("Lieferung & Kommissionierung")


# -----------------------------------------------------------------------------
# Login-Schranke
# Wenn niemand angemeldet ist, zeigen wir nur die Login-Seite und stoppen hier.
# st.stop() bricht den restlichen Code ab, damit die App nicht weiterläuft.
# -----------------------------------------------------------------------------
if not st.session_state.get("eingeloggt", False):
    login.anzeigen()
    st.stop()


# Ab hier ist sicher jemand angemeldet.
benutzer = st.session_state["benutzer"]
rolle = st.session_state["rolle"]


# -----------------------------------------------------------------------------
# Seitenleiste: Navigation
# -----------------------------------------------------------------------------
st.sidebar.header("Navigation")

st.sidebar.write(f"**Angemeldet als:** {benutzer}")
st.sidebar.write(f"**Rolle:** {rolle}")

st.sidebar.markdown("---")

seite = st.sidebar.radio(
    "Ansicht auswählen",
    [
        "Aufträge",
        "Lieferschein",
        "Pickliste",
        "Eventlog",
    ]
)

st.sidebar.markdown("---")

# Logout: Session leeren und neu laden -> landet wieder auf der Login-Seite
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()


# -----------------------------------------------------------------------------
# Hauptbereich
# -----------------------------------------------------------------------------
if seite == "Aufträge":
    offene_auftraege.anzeigen()

elif seite == "Lieferschein":
    lieferschein.anzeigen()

elif seite == "Pickliste":
    pickliste.anzeigen()

elif seite == "Eventlog":
    eventlog.anzeigen()