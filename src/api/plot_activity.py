import matplotlib.pyplot as plt
import io
from datetime import datetime
from fastapi.responses import StreamingResponse
import matplotlib.ticker as ticker
from common.config import GARMIN_ACTIVITIES
from common.connection_helper import db_connection

def generate_activity_plot(activity_id: str):
    query = """
        SELECT
            timestamp,
            distance,
            cadence,
            altitude,
            hr,
            rr,
            speed,
            temperature
        FROM activity_records
        WHERE activity_id = ?
        ORDER BY record
    """
    with db_connection(GARMIN_ACTIVITIES) as conn:
        rows = conn.execute(query, (activity_id,)).fetchall()

    if not rows:
        raise ValueError("Aucune donnée trouvée pour cette activité.")

    timestamps = [datetime.fromisoformat(row["timestamp"]) for row in rows]

    if timestamps:
        duration = timestamps[-1] - timestamps[0]
        total_minutes = int(duration.total_seconds() // 60)
        total_hours = total_minutes // 60
        total_minutes = total_minutes % 60
        duration_str = f"{total_hours}h {total_minutes}min" if total_hours else f"{total_minutes} min"
    else:
        duration_str = "Durée inconnue"


    metrics = {
        "Cadence": [row["cadence"] for row in rows],
        #"Altitude (m)": [row["altitude"] for row in rows],
        "FC (bpm)": [row["hr"] for row in rows],
        "RR (ms)": [row["rr"] for row in rows],
        "Allure (min/km)": [((60 / row["speed"])) if row["speed"] and row["speed"] > 0 else None for row in rows],
        "Température (°C)": [row["temperature"] for row in rows],
    }

    # Supprimer les métriques sans aucune valeur
    filtered_metrics = {
        label: values for label, values in metrics.items()
        if any(v is not None for v in values)
    }

    fig = plt.figure(figsize=(15, 8))
    try:
        for label, values in filtered_metrics.items():
            plt.plot(timestamps, values, label=label)

        plt.xlabel("Temps")
        plt.ylabel("Valeurs")
        plt.title(f"Activité {activity_id} - Détails")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        ax = plt.gca()
        ax.axhspan(104, 145, facecolor='green', alpha=0.1, label='Zone 1')
        ax.axhspan(145, 166, facecolor='yellow', alpha=0.1, label='Zone 2')
        ax.axhspan(166, 181, facecolor='orange', alpha=0.1, label='Zone 3')
        ax.axhspan(181, 194, facecolor='red', alpha=0.1, label='Zone 4')
        ax.axhspan(194, 210, facecolor='purple', alpha=0.1, label='Zone 5')

        ax.yaxis.set_major_locator(ticker.MultipleLocator(5))

        distance_values = [row["distance"] for row in rows if row["distance"] is not None]
        total_distance_km = distance_values[-1] if distance_values else 0
        plt.annotate(
            f"{total_distance_km:.2f} km en {duration_str}",
            xy=(1.0, 1.02),
            xycoords='axes fraction',
            fontsize=10,
            ha='right',
            va='bottom',
            bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", lw=1)
        )

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
    finally:
        plt.close(fig)

    return StreamingResponse(buf, media_type="image/png")
