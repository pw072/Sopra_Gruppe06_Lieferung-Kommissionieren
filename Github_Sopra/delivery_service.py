from datetime import date
from db import fetch_df, execute_scalar, execute_non_query


def get_kundenauftraege(modus="Offen"):
    """
    Lädt Kundenaufträge je nach Modus:
      "Offen"      -> noch nicht abgeschlossen (73) oder storniert (74)
      "Completed"  -> Status COMPLETED (73)

    Zusätzlich pro Auftrag:
      LieferscheinID         -> ID des (neuesten) Lieferscheins, falls vorhanden
      Lieferstatus           -> lesbarer Status des Lieferscheins
      LieferscheinStatusCode -> Roh-Code (intern für die COMPLETED-Regel)
    """
    if modus == "Completed":
        where = "so.SO_STATUS = 73"
    else:
        where = "(so.SO_STATUS IS NULL OR so.SO_STATUS NOT IN (73, 74))"

    sql = f"""
        SELECT
            so.ORDER_ID AS KundenauftragID,
            c.COMPANY_NAME AS Kunde,
            ISNULL(lso.ORDER_STATUS, CAST(so.SO_STATUS AS NVARCHAR(50))) AS Auftragsstatus,
            COUNT(soi.ORDER_ITEM_ID) AS AnzahlPositionen,
            (
                SELECT TOP 1 d.DELIVERY_ID
                FROM dbo.T_DELIVERY d
                WHERE d.ORDER_ID = so.ORDER_ID
                ORDER BY d.DELIVERY_ID DESC
            ) AS LieferscheinID,
            (
                SELECT TOP 1 COALESCE(lsd.DELIVERY_STATUS, CAST(d.STATUS AS NVARCHAR(50)))
                FROM dbo.T_DELIVERY d
                LEFT JOIN dbo.LOV_STATUS_DELIVERY lsd
                    ON TRY_CONVERT(INT, d.STATUS) = lsd.CODE_ID
                WHERE d.ORDER_ID = so.ORDER_ID
                ORDER BY d.DELIVERY_ID DESC
            ) AS Lieferstatus,
            (
                SELECT TOP 1 d.STATUS
                FROM dbo.T_DELIVERY d
                WHERE d.ORDER_ID = so.ORDER_ID
                ORDER BY d.DELIVERY_ID DESC
            ) AS LieferscheinStatusCode
        FROM dbo.T_SALESORDER so

        INNER JOIN dbo.T_SALESORDER_ITEMS soi
            ON so.ORDER_ID = soi.ORDER_ID

        LEFT JOIN dbo.LOV_STATUS_ORDER lso
            ON so.SO_STATUS = lso.CODE_ID

        LEFT JOIN dbo.T_SALESOFFER sf
            ON so.SALESOFFER_ID = sf.SALESOFFER_ID

        LEFT JOIN dbo.T_CUSTOMER c
            ON sf.CUSTOMER_ID = c.CUSTOMER_ID

        WHERE {where}

        GROUP BY
            so.ORDER_ID,
            c.COMPANY_NAME,
            lso.ORDER_STATUS,
            so.SO_STATUS,
            so.INS_DATE

        ORDER BY
            so.INS_DATE DESC,
            so.ORDER_ID DESC
    """

    return fetch_df(sql)


def get_kundenauftrag_positionen(order_id):
    sql = """
        SELECT
            soi.ORDER_ITEM_ID AS Position,
            m.MAT_NR AS Artikelnummer,
            m.MAT_DESCR AS Artikelbezeichnung,
            soi.QUANTITY AS Menge,
            m.MAT_STOCK_AMOUNT AS Lagerbestand,
            CASE
                WHEN m.MAT_STOCK_AMOUNT >= soi.QUANTITY THEN 'Ja'
                ELSE 'Nein'
            END AS VollstaendigVerfuegbar
        FROM dbo.T_SALESORDER_ITEMS soi

        INNER JOIN dbo.T_MATERIAL m
            ON soi.MAT_ID = m.ID_MAT

        WHERE soi.ORDER_ID = ?

        ORDER BY soi.ORDER_ITEM_ID
    """

    return fetch_df(sql, (order_id,))


def lieferschein_aus_auftrag_erstellen(order_id, benutzer):
    sql = """
        DECLARE @neue_delivery_id INT;

        EXEC dbo.sp_ins_delivery_from_order
            @order_id = ?,
            @delivery_date = ?,
            @caller = ?,
            @delivery_id = @neue_delivery_id OUTPUT;

        SELECT @neue_delivery_id AS DELIVERY_ID;
    """

    neue_delivery_id = execute_scalar(
        sql,
        (
            order_id,
            date.today(),
            benutzer
        )
    )

    return neue_delivery_id


# -----------------------------------------------------------------------------
# Lieferscheine anzeigen
# -----------------------------------------------------------------------------

def get_lieferscheine():
    """Eine Zeile pro Lieferschein (nur Kopfdaten) für die Übersicht."""
    sql = """
        SELECT DISTINCT
            LieferscheinID,
            KundenauftragID,
            Kundenfirma,
            Lieferdatum,
            Lieferstatus
        FROM dbo.V_LIST_LIEFERSCHEIN
        ORDER BY LieferscheinID DESC
    """
    return fetch_df(sql)


def get_lieferschein_details(lieferschein_id):
    """Alle Daten zu einem Lieferschein, inklusive Positionen."""
    sql = """
        SELECT
            LieferscheinID,
            KundenauftragID,
            Kundenfirma,
            Ansprechpartner,
            Lieferadresse_Strasse,
            Lieferadresse_PLZ,
            Lieferadresse_Ort,
            Lieferadresse_Bundesland,
            Absenderadresse,
            Lieferdatum,
            Lieferstatus,
            Artikelnummer,
            Artikelbezeichnung,
            Menge
        FROM dbo.V_LIST_LIEFERSCHEIN
        WHERE LieferscheinID = ?
        ORDER BY Artikelnummer
    """
    return fetch_df(sql, (lieferschein_id,))


# -----------------------------------------------------------------------------
# NEU: Lieferschein-Status ändern
# -----------------------------------------------------------------------------

def get_lieferschein_status_auswahl():
    """Alle möglichen Lieferstatus für das Dropdown (CODE_ID + Anzeigetext)."""
    sql = """
        SELECT
            CODE_ID,
            DELIVERY_STATUS
        FROM dbo.LOV_STATUS_DELIVERY
        ORDER BY CODE_ID
    """
    return fetch_df(sql)


def lieferschein_status_aendern(delivery_id, neuer_status_id, benutzer):
    """
    Ruft sp_upd_delivery_status auf.
    Die Prüfung der erlaubten Statusfolge passiert in der Prozedur selbst.
    """
    sql = """
        EXEC dbo.sp_upd_delivery_status
            @delivery_id = ?,
            @newstatus_id = ?,
            @caller = ?;
    """
    execute_non_query(
        sql,
        (
            delivery_id,
            neuer_status_id,
            benutzer
        )
    )


# -----------------------------------------------------------------------------
# NEU: Auftragsstatus ändern (73 = COMPLETED, 74 = CANCELED)
# -----------------------------------------------------------------------------

def kundenauftrag_status_aendern(order_id, neuer_status_id, benutzer):
    """
    Setzt den Status eines Kundenauftrags in T_SALESORDER.
    Die Regel (COMPLETED nur bei DELIVERED) wird in der Ansicht geprüft,
    bevor diese Funktion aufgerufen wird.
    Der Trigger trg_salesorder_log schreibt die Änderung automatisch ins Eventlog.
    """
    sql = """
        UPDATE dbo.T_SALESORDER
        SET SO_STATUS = ?,
            UPD_USER = ?,
            UPD_DATE = GETDATE()
        WHERE ORDER_ID = ?
    """
    execute_non_query(
        sql,
        (
            neuer_status_id,
            benutzer,
            order_id
        )
    )