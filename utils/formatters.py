def normalizar_numero(valor) -> float:
    """Convierte un valor de tipo texto o numérico a float limpiando caracteres especiales."""
    if valor is None or valor == "":
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    val_str = str(valor).strip().replace("$", "").replace(".", "").replace(",", ".")
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def asegurar_float(val) -> float:
    """Garantiza la conversión de cualquier entrada a tipo float seguro."""
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

def formato_moneda(valor: float) -> str:
    """Retorna un número formateado como moneda ($1.234,56)."""
    val = asegurar_float(valor)
    return f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
