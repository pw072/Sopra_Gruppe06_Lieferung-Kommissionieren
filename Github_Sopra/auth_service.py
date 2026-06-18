from db import fetch_df


def pruefe_login(username, passwort):
    """
    Prüft Benutzername und Passwort gegen die Tabelle T_USER.
    Gibt True zurück, wenn genau dieser Benutzer mit diesem Passwort
    existiert, sonst False.
    """
    sql = """
        SELECT COUNT(*) AS Treffer
        FROM dbo.T_USER
        WHERE USERNAME = ?
          AND USERPASS = ?
    """
    ergebnis = fetch_df(sql, (username, passwort))
    return int(ergebnis["Treffer"].iloc[0]) > 0