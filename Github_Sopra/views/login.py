import streamlit as st

from auth_service import pruefe_login
from permissions import rolle_fuer_benutzer


def anzeigen():
    st.header("Anmeldung")
    st.write("Bitte mit Benutzername und Passwort anmelden.")

    username = st.text_input("Benutzername")
    passwort = st.text_input("Passwort", type="password")

    if st.button("Anmelden"):
        try:
            if pruefe_login(username, passwort):
                # Anmeldung erfolgreich -> Benutzer und Rolle merken
                st.session_state["eingeloggt"] = True
                st.session_state["benutzer"] = username
                st.session_state["rolle"] = rolle_fuer_benutzer(username)
                st.rerun()
            else:
                st.error("Benutzername oder Passwort ist falsch.")
        except Exception as fehler:
            st.error("Die Anmeldung konnte nicht geprüft werden.")
            st.exception(fehler)