import sys
import pandas as pd

def is_warm(row, sensor_cols):
    """Devuelve True si al menos una columna de sensor tiene datos reales."""
    for col in sensor_cols:
        val = row.get(col, "Sin registro")
        if pd.isna(val):
            continue
        str_val = str(val).strip().lower()
        if str_val not in ("sin registro", "no detectado", "0", "", "nan"):
            return True
        try:
            if float(val) != 0.0:
                return True
        except (ValueError, TypeError):
            pass
    return False

def find_warmup_end(df):
    sensor_cols = [
        "# palabras leidas", "emocion_principal", "confianza",
        "segunda_emocion", "direccion", "retencion"
    ]
    sensor_cols = [c for c in sensor_cols if c in df.columns]

    for i, (_, row) in enumerate(df.iterrows()):
        palabras = row.get("# palabras leidas", 0)
        try:
            if float(palabras) > 0:
                return i
        except (ValueError, TypeError):
            pass
        if is_warm(row, sensor_cols):
            return i

    return 0

def merge_session_data(unity_path, emotions_path, eyetracking_path, output_path):
    df_unity = pd.read_csv(unity_path)
    df_emo   = pd.read_csv(emotions_path)
    df_eye   = pd.read_csv(eyetracking_path)

    df_final = pd.merge(df_unity, df_emo, on="timestamp", how="outer")
    df_final = pd.merge(df_final, df_eye, on="timestamp", how="outer")

    if "contador_x" in df_final.columns:
        df_final = df_final.rename(columns={"contador_x": "contador_segundos"})

    columnas_basura = [
        col for col in df_final.columns
        if col.startswith("contador_") and col != "contador_segundos"
    ]
    df_final = df_final.drop(columns=columnas_basura, errors="ignore")

    if "contador" in df_final.columns:
        df_final = df_final.drop(columns=["contador"])

    df_final = df_final.sort_values("timestamp").reset_index(drop=True)
    df_final = df_final.fillna("Sin registro")

    # --- Limpieza del período de arranque ---
    warmup_end = find_warmup_end(df_final)
    if warmup_end > 0:
        print(f"[MergeMetrics] Eliminando {warmup_end} fila(s) de arranque (warmup).")
        df_final = df_final.iloc[warmup_end:].reset_index(drop=True)

    if "contador_segundos" in df_final.columns:
        df_final["contador_segundos"] = range(1, len(df_final) + 1)
        df_final = df_final.rename(columns={"contador_segundos": "contador"})

    df_final.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[MergeMetrics] ¡Éxito! CSV maestro generado en: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Uso correcto: python merge_metrics.py <unity.csv> <emociones.csv> <eyetracking.csv> <salida.csv>")
        sys.exit(1)
    try:
        merge_session_data(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    except Exception as e:
        print(f"[MergeMetrics] Error crítico: {e}", file=sys.stderr)
        sys.exit(1)