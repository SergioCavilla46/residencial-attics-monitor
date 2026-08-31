import argparse
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.residencialatics.com/viviendas"

# Topic de producción
NTFY_TOPIC = "sergio-attics-2-2713"

# Topic exclusivo para pruebas
NTFY_TEST_TOPIC = "sergio-attics-test-2-2713"

NTFY_BASE_URL = "https://ntfy.sh"

STATE_FILE = "state.json"

TEST_HTML_FILE = "tests/fixtures/residencial_actual.html"
TEST_STATE_FILE = "tests/state_before.json"

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


def get_homes(test_mode=False):
    """
    Obtiene las viviendas.

    Producción:
        Descarga la web real.

    Test:
        Utiliza el HTML guardado en tests/fixtures/.
    """

    if test_mode:
        print("Usando HTML local de prueba...")

        if not os.path.exists(TEST_HTML_FILE):
            raise FileNotFoundError(
                f"No existe la fixture de prueba: {TEST_HTML_FILE}"
            )

        with open(TEST_HTML_FILE, "r", encoding="utf-8") as f:
            html = f.read()

    else:
        response = requests.get(
            URL,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        html = response.text

    soup = BeautifulSoup(html, "html.parser")

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

            vivienda_num = vivienda.replace(
                "Vivienda ",
                ""
            ).strip()

            key = f"bloque-{block_number}-vivienda-{vivienda_num}"

            price = parse_price(precio)

            status = (
                "reserved"
                if price is None
                else "available"
            )

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


def load_state(test_mode=False):
    """
    Carga el estado anterior.

    Producción:
        state.json

    Test:
        tests/state_before.json
    """

    state_file = (
        TEST_STATE_FILE
        if test_mode
        else STATE_FILE
    )

    if not os.path.exists(state_file):
        return None

    with open(state_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(homes, test_mode=False):
    """
    Guarda el nuevo estado.

    En producción:
        actualiza state.json.

    En test:
        no modifica el estado de prueba, para que el escenario
        sea reproducible en ejecuciones posteriores.
    """

    if test_mode:
        print("MODO TEST: estado de prueba no modificado.")
        return

    data = {
        "last_check": datetime.now().isoformat(),
        "homes": homes
    }

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def get_ntfy_url(test_mode=False):
    """
    Devuelve el endpoint de ntfy correspondiente al entorno.

    IMPORTANTE:
    El modo test utiliza exclusivamente el topic de pruebas.
    """

    topic = (
        NTFY_TEST_TOPIC
        if test_mode
        else NTFY_TOPIC
    )

    # Protección adicional contra errores de configuración.
    if test_mode and topic == NTFY_TOPIC:
        raise RuntimeError(
            "ERROR DE SEGURIDAD: el modo test no puede utilizar "
            "el topic de producción."
        )

    return f"{NTFY_BASE_URL}/{topic}"


def send_ntfy(message, test_mode=False):
    """
    Envía una notificación a ntfy.

    Producción:
        Topic productivo.

    Test:
        Topic exclusivo de pruebas.
    """

    ntfy_url = get_ntfy_url(test_mode)

    if test_mode:
        message = (
            "🧪 TEST — RESIDENCIAL ÁTICOS\n\n"
            + message
        )

    response = requests.post(
        ntfy_url,
        data=message.encode("utf-8"),
    headers={
        "Title": (
            "TEST - Residencial Aticos"
            if test_mode
            else "Residencial Aticos"
        ),
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
        1
        for home in homes.values()
        if home["status"] == "reserved"
    )

    available = total - reserved

    percentage = (
        reserved / total * 100
        if total
        else 0
    )

    return (
        total,
        reserved,
        available,
        percentage
    )


def main():

    parser = argparse.ArgumentParser(
        description="Monitor de viviendas de Residencial Áticos."
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help=(
            "Ejecuta el monitor usando la fixture y el estado "
            "de prueba, enviando las notificaciones al topic de test."
        )
    )

    args = parser.parse_args()

    test_mode = args.test

    if test_mode:

        print()
        print("========================================")
        print(" MODO TEST")
        print("========================================")
        print(f"HTML:  {TEST_HTML_FILE}")
        print(f"STATE: {TEST_STATE_FILE}")
        print(f"NTFY:  {NTFY_TEST_TOPIC}")
        print("========================================")
        print()

    else:

        print("Consultando Residencial Áticos...")

    homes = get_homes(test_mode)

    total, reserved, available, percentage = sales_summary(
        homes
    )

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

    old_state = load_state(test_mode)

    # Primera ejecución
    if old_state is None:

        save_state(
            homes,
            test_mode
        )

        print("Primera ejecución.")
        print("Estado inicial guardado.")
        print("No se enviarán notificaciones.")

        return

    old_homes = old_state.get(
        "homes",
        {}
    )

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

        # CAMBIO DE PRECIO
        elif (
            previous["price"] is not None
            and current["price"] is not None
            and previous["price"] != current["price"]
        ):

            difference = (
                current["price"]
                - previous["price"]
            )

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

        message = (
            summary
            + "\n\n".join(events)
        )

        try:

            send_ntfy(
                message,
                test_mode
            )

            if test_mode:
                print(
                    "Notificación de TEST enviada "
                    "al topic de pruebas."
                )
            else:
                print(
                    "Notificación enviada a ntfy."
                )

        except Exception as e:

            print(
                f"Error enviando ntfy: {e}"
            )

    else:

        print("Sin cambios.")

    save_state(
        homes,
        test_mode
    )

    print("Estado actualizado.")

    if test_mode:
        print(
            "El estado de producción "
            "no ha sido modificado."
        )


if __name__ == "__main__":
    main()