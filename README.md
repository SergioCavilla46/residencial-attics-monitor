# Residencial Áticos Monitor
Monitor automático de las viviendas disponibles de la promoción Residencial Áticos.
El proyecto consulta periódicamente la página de viviendas, compara el estado actual con el estado de la última ejecución y envía una notificación mediante [ntfy](https://ntfy.sh/) cuando detecta cambios relevantes.
Actualmente el monitor se ejecuta mediante `cron-job.org`, que dispara manualmente el workflow de GitHub Actions mediante la API de GitHub.
---
## Funcionalidades
El monitor obtiene de la web:
- Número de vivienda
- Bloque
- Planta
- Dormitorios
- Baños
- Garaje
- Trastero
- Superficie construida
- Superficie de terraza
- Precio
- Estado de la vivienda
Actualmente detecta tres tipos de cambios:
### Nueva reserva
Cuando una vivienda pasa de:
```text
available → reserved

se envía una notificación:

🔴 NUEVA RESERVA

Vivienda vuelve a estar disponible

Cuando una vivienda pasa de:

reserved → available

se envía:

🟢 VIVIENDA VUELVE A ESTAR DISPONIBLE

Cambio de precio

Si una vivienda continúa disponible pero cambia su precio, se envía:

💰 CAMBIO DE PRECIO

indicando:

* Precio anterior
* Precio nuevo
* Diferencia
* Características de la vivienda

⸻

Estructura del proyecto

residencial-attics-monitor/
│
├── .github/
│   └── workflows/
│       └── monitor.yml
│
├── tests/
│   ├── fixtures/
│   │   └── residencial_actual.html
│   └── state_before.json
│
├── .gitignore
├── README.md
├── requirements.txt
├── state.json
└── web_check.py

Archivos

web_check.py

Script principal del monitor.

Se encarga de:

1. Descargar o cargar el HTML.
2. Extraer las viviendas mediante BeautifulSoup.
3. Comparar el estado actual con el estado anterior.
4. Detectar reservas, viviendas liberadas y cambios de precio.
5. Enviar notificaciones a ntfy.
6. Actualizar el estado.

También incluye un modo de prueba reproducible mediante:

python3 web_check.py --test

⸻

state.json

Estado utilizado en producción.

Contiene la última información conocida de todas las viviendas y la fecha de la última comprobación.

Este archivo se actualiza automáticamente durante las ejecuciones de producción.

Ejemplo:

{
  "last_check": "2026-08-31T18:15:31.176545",
  "homes": {
    "bloque-1-vivienda-1": {
      "block": 1,
      "home": 1,
      "status": "available"
    }
  }
}

El estado se mantiene en Git para que GitHub Actions pueda conservarlo entre ejecuciones.

⸻

requirements.txt

Dependencias de Python:

requests
beautifulsoup4

Instalación:

pip install -r requirements.txt

⸻

.github/workflows/monitor.yml

Workflow de GitHub Actions.

Actualmente utiliza únicamente:

on:
  workflow_dispatch:

No utiliza schedule.

Esto permite que el workflow sea ejecutado externamente mediante la API de GitHub.

⸻

GitHub Actions + cron-job.org

El workflow se ejecuta automáticamente mediante cron-job.org.

La arquitectura es:

cron-job.org
      │
      │ HTTP POST
      ▼
GitHub API
      │
      │ workflow_dispatch
      ▼
GitHub Actions
      │
      ▼
web_check.py
      │
      ├── consulta web
      ├── compara state.json
      └── ntfy

Esto permite controlar externamente la frecuencia de ejecución.

Actualmente el objetivo es ejecutar el monitor cada 15 minutos.

⸻

Configuración de cron-job.org

1. Crear un Personal Access Token de GitHub

GitHub necesita autenticar la petición que realiza cron-job.org.

En GitHub:

Settings
→ Developer Settings
→ Personal access tokens
→ Tokens (classic)
→ Generate new token

Crear un token con una descripción, por ejemplo:

cron-job-trigger

Debe tener permiso:

workflow

Copiar el token inmediatamente después de crearlo.

No debe almacenarse en el repositorio.

⸻

2. Configurar el workflow

El workflow debe permitir ejecución manual:

name: Residencial Aticos Monitor
on:
  workflow_dispatch:
permissions:
  contents: write

No se debe añadir schedule si se utiliza cron-job.org como sistema externo de planificación.

⸻

3. Crear el cronjob

Acceder a:

https://cron-job.org/

Crear un nuevo Cronjob.

Title

Residencial Monitor Trigger

URL

Utilizar la API de GitHub:

https://api.github.com/repos/TU_USUARIO/TU_REPOSITORIO/actions/workflows/monitor.yml/dispatches

En este proyecto:

https://api.github.com/repos/SergioCavilla46/residencial-attics-monitor/actions/workflows/monitor.yml/dispatches

Schedule

Configurar:

Every 15 minutes

⸻

4. Configurar la petición HTTP

Método:

POST

Body:

{
  "ref": "main"
}

Headers:

Authorization: Bearer TU_TOKEN
Accept: application/vnd.github+json
User-Agent: cron-job-org

El token debe mantenerse privado.

⸻

5. Probar cron-job.org

Desde cron-job.org ejecutar el trabajo manualmente mediante Run now o Test.

Una respuesta:

HTTP 204 No Content

significa que GitHub ha aceptado correctamente la petición de ejecución.

Después se puede comprobar la ejecución desde:

GitHub
→ Actions
→ Residencial Aticos Monitor

⸻

Notificaciones mediante ntfy

El proyecto utiliza ntfy para enviar notificaciones.

Topic de producción:

sergio-attics-2-2713

El dispositivo móvil debe estar suscrito a este topic para recibir las alertas de producción.

No se necesitan credenciales para utilizar un topic público de ntfy, por lo que el nombre del topic debe considerarse no secreto.

⸻

Entorno de pruebas

El proyecto dispone de un entorno de pruebas reproducible.

Su objetivo es poder comprobar la lógica del monitor sin esperar a que una vivienda cambie realmente de estado en la web.

El entorno utiliza:

tests/
├── fixtures/
│   └── residencial_actual.html
└── state_before.json

residencial_actual.html

Es una copia congelada del HTML real de la página de viviendas en el momento en el que se creó el escenario.

Esto permite ejecutar el parser contra una versión estable de la web.

state_before.json

Representa el estado anterior al HTML guardado.

Modificando este archivo se pueden simular cambios que realmente no han ocurrido todavía en la web.

⸻

Ejecutar una prueba

El modo de prueba se ejecuta con:

python3 web_check.py --test

En este modo:

* No se consulta Internet.
* Se utiliza tests/fixtures/residencial_actual.html.
* Se utiliza tests/state_before.json.
* No se modifica state.json.
* No se modifica tests/state_before.json.
* Las notificaciones utilizan un topic separado.

Topic de pruebas:

sergio-attics-test-2-2713

El mensaje se identifica como:

🧪 TEST — RESIDENCIAL ÁTICOS

⸻

Simular una nueva reserva

Para simular una vivienda que pasa de disponible a reservada:

1. Crear una copia de seguridad del escenario:

cp tests/state_before.json tests/state_before.json.backup

2. Abrir:

nano tests/state_before.json

3. Buscar una vivienda:

"status": "available"

4. Cambiarla a:

"status": "reserved"

5. Ejecutar:

python3 web_check.py --test

El HTML congelado seguirá indicando que la vivienda está disponible, mientras que el estado anterior indicará que estaba reservada.

El monitor detectará:

reserved → available

y enviará:

🟢 VIVIENDA VUELVE A ESTAR DISPONIBLE

Para simular el caso contrario, cambiar available a reserved en el estado anterior. El monitor detectará:

available → reserved

y enviará:

🔴 NUEVA RESERVA

⸻

Restaurar el escenario de pruebas

Después de realizar una prueba:

cp tests/state_before.json.backup tests/state_before.json

El escenario vuelve a su estado inicial.

El archivo:

tests/state_before.json.backup

está excluido de Git mediante .gitignore.

⸻

Ejecución local en producción

Para ejecutar el monitor directamente contra la web real:

python3 web_check.py

El flujo es:

Web real
   ↓
web_check.py
   ↓
state.json
   ↓
Comparación
   ↓
ntfy producción

La primera ejecución no genera notificaciones porque no existe todavía un estado anterior.

En su lugar, crea:

state.json

A partir de las siguientes ejecuciones se empiezan a detectar cambios.

⸻

Desarrollo local

Crear un entorno virtual:

python3 -m venv .venv

Activarlo:

source .venv/bin/activate

Instalar dependencias:

pip install -r requirements.txt

Ejecutar producción:

python3 web_check.py

Ejecutar pruebas:

python3 web_check.py --test

⸻

Git

El repositorio utiliza main como rama principal.

Para actualizar el repositorio local:

git fetch origin
git pull --rebase origin main

Para subir cambios:

git add .
git commit -m "Descripción del cambio"
git push origin main

Si GitHub contiene commits que no existen localmente, no utilizar git push --force directamente.

Primero:

git fetch origin
git rebase origin/main

y después:

git push origin main

Esto permite conservar tanto los commits generados por el monitor como los cambios realizados localmente.

⸻

Flujo completo

El funcionamiento final del proyecto es:

                    cron-job.org
                         │
                    cada 15 min
                         │
                         ▼
                 GitHub API
                         │
                 workflow_dispatch
                         │
                         ▼
                 GitHub Actions
                         │
                         ▼
                  web_check.py
                         │
                  consulta la web
                         │
                         ▼
                  compara state.json
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
          Reserva    Disponible   Precio
              │          │          │
              └──────────┼──────────┘
                         │
                         ▼
                    ntfy.sh
                         │
                         ▼
                      Móvil

El entorno de pruebas queda separado:

python3 web_check.py --test
              │
              ▼
tests/fixtures/residencial_actual.html
              │
              ▼
tests/state_before.json
              │
              ▼
       detección de evento
              │
              ▼
sergio-attics-test-2-2713

De esta forma, producción y pruebas utilizan exactamente la misma lógica del monitor, pero tienen fuentes de datos, estados y canales de notificación independientes.


