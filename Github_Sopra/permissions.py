# -----------------------------------------------------------------------------
# Welche Rolle darf welche Aktion ausführen?
# -----------------------------------------------------------------------------
ROLE_PERMISSIONS = {
    "Sachbearbeiter": {
        "view",
        "check_stock",
    },
    "Fachkraft": {
        "view",
        "check_stock",
        "create_picklist",
        "create_delivery",
        "start_picking",
        "finish_picking",
        "book_goods_issue",
    },
    "Teamleiter": {
        "view",
        "check_stock",
        "create_picklist",
        "create_delivery",
        "start_picking",
        "finish_picking",
        "book_goods_issue",
        "cancel_delivery",
        "mark_delivered",
        "return_delivery",
        "complete_order",
        "cancel_order",
    },
}


# -----------------------------------------------------------------------------
# Zuordnung: welcher Benutzer hat welche Rolle?
#
# In T_USER ist keine Rolle (Sachbearbeiter/Fachkraft/Teamleiter) gespeichert.
# Deshalb legen WIR hier fest, wer welche Rolle bekommt.
# Tragt eure Test-Benutzer hier ein. Wer nicht in der Liste steht,
# bekommt automatisch die Standardrolle.
# Zum Testen einer Rolle einfach den Wert hier ändern und neu anmelden.
# -----------------------------------------------------------------------------
USER_ROLES = {
    "s26s521": "Teamleiter",
    # "s26s540": "Fachkraft",
    # "moritz":  "Sachbearbeiter",
}

STANDARD_ROLLE = "Sachbearbeiter"


def rolle_fuer_benutzer(username):
    """Gibt die Rolle zum Benutzer zurück (oder die Standardrolle)."""
    return USER_ROLES.get(username, STANDARD_ROLLE)


def can(role, action):
    """True, wenn die Rolle die Aktion ausführen darf."""
    return action in ROLE_PERMISSIONS.get(role, set())