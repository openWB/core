class PermanentTariffError(Exception):
    """Fehler, der sich durch erneutes Abrufen nicht beheben lässt (z.B. falsche Zugangsdaten).
    Der Tarif wird erst nach einer Änderung der Konfiguration wieder abgefragt."""
