import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.residencialatics.com/viviendas"

NTFY_TOPIC = "sergio-attics-2-2713"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    )
}


def parse_price(value):
    value = value.strip()

    if value.upper() == "RESERVADO":
        return None

    value = (
        value.replace("€", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    try:
        return float(value)
    except ValueError:
        return None


def format_price(price):
    if price is None:
        return "RESERVADO"

    return f"{price:,.0f} €".replace(",", ".")


def clean(value):
    return value.replace("\xa0", " ").strip()


def get_homes():
    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table")

    homes = {}

    # Las tres primeras tablas corresponden a los tres bloques/promociones
    for block_number, table in enumerate(tables[:3], start=1):

        rows = table.find_all("tr")

        for row in rows[1:]:
            cells = [
                clean(cell.get_text(" ", strip=True))
                for cell in row.find_all(["th", "td"])
            ]

            if len(cells) < 10:
                continue

            (
                vivienda,
                planta,
                dormitorios,
                banos,
                garaje,
                trastero,
                superficie,
                terraza,
                plano,
                precio
            ) = cells[:10]

            vivienda_num = vivienda.replace("Vivienda ", "").strip()

            key = f"bloque-{block_number}-vivienda-{vivienda_num}"

            price = parse_price(precio)

            status = "reserved" if price is None else "available"

            homes[key] = {
                "block": block_number,
                "home": int(vivienda_num),
                "floor": planta,
                "bedrooms": int(dormitorios),
                "bathrooms": int(banos),
                "garage": garaje,
                "storage": trastero,
                "surface": superficie,
                "terrace": terraza,
                "price": price,
                "status": status
            }

    return homes


def load_state():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(homes):
    data = {
        "last_check": datetime.now().isoformat(),
        "homes": homes
    }

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_ntfy(message):
    response = requests.post(
        NTFY_URL,
        data=message.encode("utf-8"),
        headers={
            "Title": "Residencial Áticos",
            "Priority": "default",
            "Tags": "house"
        },
        timeout=15
    )

    response.raise_for_status()


def home_description(home):
    return (
        f"Bloque {home['block']} · Vivienda {home['home']}\n"
        f"{home['floor']}\n"
        f"{home['bedrooms']} dormitorios · "
        f"{home['bathrooms']} baños\n"
        f"{home['surface']} m² construidos\n"
        f"{home['terrace']} m² terraza\n"
        f"Garaje: {home['garage']}\n"
        f"Trastero: {home['storage']}\n"
        f"Precio: {format_price(home['price'])}"
    )


def sales_summary(homes):
    total = len(homes)
    reserved = sum(
        1 for home in homes.values()
        if home["status"] == "reserved"
    )

    available = total - reserved

    percentage = (reserved / total * 100) if total else 0

    return (
        total,
        reserved,
        available,
        percentage
    )


def main():

    print("Consultando Residencial Áticos...")

    homes = get_homes()

    total, reserved, available, percentage = sales_summary(homes)

    print()
    print("========================================")
    print(" RESIDENCIAL ÁTICOS")
    print("========================================")
    print(f"Total:       {total}")
    print(f"Reservadas:  {reserved}")
    print(f"Disponibles: {available}")
    print(f"Vendido:     {percentage:.1f}%")
    print("========================================")
    print()

    old_state = load_state()

    # Primera ejecución
    if old_state is None:

        save_state(homes)

        print("Primera ejecución.")
        print("Estado inicial guardado.")
        print("No se enviarán notificaciones.")

        return

    old_homes = old_state.get("homes", {})

    events = []

    for key, current in homes.items():

        previous = old_homes.get(key)

        # Vivienda nueva que no estaba en el estado anterior
        if previous is None:
            continue

        # DISPONIBLE -> RESERVADO
        if (
            previous["status"] == "available"
            and current["status"] == "reserved"
        ):

            events.append(
                "🔴 NUEVA RESERVA\n\n"
                + home_description(current)
            )

        # RESERVADO -> DISPONIBLE
        elif (
            previous["status"] == "reserved"
            and current["status"] == "available"
        ):

            events.append(
                "🟢 VIVIENDA VUELVE A ESTAR DISPONIBLE\n\n"
                + home_description(current)
            )

        # Cambio de precio
        elif (
            previous["price"] is not None
            and current["price"] is not None
            and previous["price"] != current["price"]
        ):

            difference = current["price"] - previous["price"]

            if difference > 0:
                change = f"+{format_price(difference)}"
            else:
                change = format_price(difference)

            events.append(
                "💰 CAMBIO DE PRECIO\n\n"
                f"Bloque {current['block']} · "
                f"Vivienda {current['home']}\n\n"
                f"Antes: {format_price(previous['price'])}\n"
                f"Ahora: {format_price(current['price'])}\n"
                f"Cambio: {change}\n\n"
                f"{current['floor']}\n"
                f"{current['bedrooms']} dormitorios · "
                f"{current['bathrooms']} baños\n"
                f"{current['surface']} m² construidos\n"
                f"{current['terrace']} m² terraza"
            )

    # Si hay eventos, mandamos un resumen
    if events:

        summary = (
            f"📊 RESIDENCIAL ÁTICOS\n\n"
            f"{reserved}/{total} viviendas reservadas\n"
            f"{percentage:.1f}% vendido\n"
            f"{available} disponibles\n\n"
        )

        message = summary + "\n\n".join(events)

        try:
            send_ntfy(message)
            print("Notificación enviada a ntfy.")

        except Exception as e:
            print(f"Error enviando ntfy: {e}")

    else:
        print("Sin cambios.")

    save_state(homes)

    print("Estado actualizado.")


if __name__ == "__main__":
    main()