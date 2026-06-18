from db import fetch_df, execute_scalar, execute_non_query


def get_picklisten():
    """Eine Zeile pro Pickliste (nur Kopfdaten) für die Übersicht."""
    sql = """
        SELECT DISTINCT
            PicklistenID,
            KundenauftragID,
            Picklistenstatus,
            Kommissionierer
        FROM dbo.V_LIST_PICKLISTE
        ORDER BY PicklistenID DESC
    """
    return fetch_df(sql)


def get_pickliste_details(pickliste_id):
    """Alle Daten zu einer Pickliste, inklusive Positionen."""
    sql = """
        SELECT
            PicklistenID,
            KundenauftragID,
            Picklistenstatus,
            Kommissionierer,
            Artikelnummer,
            Artikelbezeichnung,
            Menge
        FROM dbo.V_LIST_PICKLISTE
        WHERE PicklistenID = ?
        ORDER BY Artikelnummer
    """
    return fetch_df(sql, (pickliste_id,))


# -----------------------------------------------------------------------------
# Pickliste aus einem Kundenauftrag erstellen
# -----------------------------------------------------------------------------

def pickliste_aus_auftrag_erstellen(order_id, kommissionierer, benutzer):
    """Ruft sp_ins_pickliste_from_order auf und gibt die neue Pickliste-ID zurück."""
    sql = """
        DECLARE @neue_pickliste_id INT;

        EXEC dbo.sp_ins_pickliste_from_order
            @order_id = ?,
            @kommissionierer = ?,
            @caller = ?,
            @pickliste_id = @neue_pickliste_id OUTPUT;

        SELECT @neue_pickliste_id AS PICKLISTE_ID;
    """

    neue_pickliste_id = execute_scalar(
        sql,
        (
            order_id,
            kommissionierer,
            benutzer
        )
    )

    return neue_pickliste_id


# -----------------------------------------------------------------------------
# NEU: Pickliste-Status ändern
# -----------------------------------------------------------------------------

def get_pickliste_status_auswahl():
    """Alle möglichen Pickstatus für das Dropdown (CODE_ID + Anzeigetext)."""
    sql = """
        SELECT
            CODE_ID,
            PICKSTATUS
        FROM dbo.LOV_PICKSTATUS
        ORDER BY CODE_ID
    """
    return fetch_df(sql)


def pickliste_status_aendern(pickliste_id, neuer_status_id, benutzer):
    """
    Ruft sp_upd_pickliste_status auf.
    Die Prüfung der erlaubten Statusfolge passiert in der Prozedur selbst.
    """
    sql = """
        EXEC dbo.sp_upd_pickliste_status
            @pickliste_id = ?,
            @newstatus_id = ?,
            @caller = ?;
    """
    execute_non_query(
        sql,
        (
            pickliste_id,
            neuer_status_id,
            benutzer
        )
    )