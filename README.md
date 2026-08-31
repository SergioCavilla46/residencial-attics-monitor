Residential Attics Monitor

Monitor automatizado para detectar cambios en el estado de las viviendas de la promoción residencial y enviar una notificación cuando se detectan modificaciones.

El sistema consulta periódicamente la página de viviendas de la promoción, obtiene la información disponible, la compara con el estado almacenado anteriormente y detecta cambios, como viviendas que pasan a estar reservadas o vuelven a estar disponibles.

Cuando se detecta un cambio, se envía una notificación mediante ntfy.

Arquitectura

El funcionamiento actual del proyecto es:

                 ┌──────────────────────┐
                 │      cron-job.org     │
                 │                      │
                 │   Cada 15 minutos    │
                 └──────────┬───────────┘
                            │
                            │ HTTP POST
                            ▼
                 ┌──────────────────────┐
                 │     GitHub API       │
                 │                      │
                 │ workflow_dispatch    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │   GitHub Actions     │
                 │                      │
                 │    monitor.yml       │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │     web_check.py     │
                 │                      │
                 │ Consulta la web      │
                 │ Procesa viviendas    │
                 │ Compara estados      │
                 └──────────┬───────────┘
                            │
                   ┌────────┴────────┐
                   │                 │
                   ▼                 ▼
          ┌────────────────┐  ┌───────────────┐
          │   state.json   │  │    ntfy.sh    │
          │                │  │               │
          │ Estado previo  │  │ Notificación  │
          └────────────────┘  └───────────────┘

El código se almacena en GitHub y el workflow de GitHub Actions ejecuta el script.

La programación de las ejecuciones se realiza mediante cron-job.org, que solicita a GitHub la ejecución del workflow cada 15 minutos.

Funcionamiento

El proceso completo es:

1. cron-job.org ejecuta el cronjob cada 15 minutos.
2. cron-job.org realiza una petición POST a la API de GitHub.
3. GitHub recibe la petición workflow_dispatch.
4. GitHub Actions inicia monitor.yml.
5. El workflow ejecuta web_check.py.
6. web_check.py accede a la página de viviendas.
7. El HTML se procesa mediante BeautifulSoup.
8. Se extraen los datos de las viviendas.
9. Los datos se comparan con state.json.
10. Si existe algún cambio de estado, se envía una notificación mediante ntfy.
11. El nuevo estado se guarda en state.json.
12. Si state.json ha cambiado, GitHub Actions puede realizar un commit y subir el nuevo estado al repositorio.

Estructura del proyecto

residencial-attics-monitor/
│
├── .github/
│   └── workflows/
│       └── monitor.yml
│
├── .gitignore
├── README.md
├── requirements.txt
├── state.json
└── web_check.py

Los siguientes elementos también pueden existir localmente, pero no forman parte del código que se versiona:

.venv/
__pycache__/
*.pyc

Estos archivos están excluidos mediante .gitignore.

Ficheros

.github/workflows/monitor.yml

Workflow de GitHub Actions encargado de ejecutar el monitor.

Actualmente utiliza:

on:
  workflow_dispatch:

Esto permite que GitHub ejecute el workflow cuando recibe una petición externa a través de la API.

No se utiliza:

schedule:

La programación se delega en cron-job.org.

El workflow dispone de permisos para escribir en el repositorio:

permissions:
  contents: write

Esto permite que el workflow pueda actualizar state.json y realizar un commit cuando sea necesario.

web_check.py

Es el script principal del proyecto.

Sus responsabilidades principales son:

* Acceder a la página de viviendas.
* Descargar el contenido HTML.
* Analizar el HTML mediante BeautifulSoup.
* Extraer la información de las viviendas.
* Procesar precios.
* Identificar viviendas reservadas.
* Comparar el estado actual con el estado almacenado.
* Detectar cambios.
* Enviar notificaciones mediante ntfy.
* Actualizar state.json.

La URL consultada actualmente es:

https://www.residencialatics.com/viviendas

El script utiliza requests para realizar las peticiones HTTP y BeautifulSoup para analizar el HTML.

También define un User-Agent para realizar la petición de forma similar a un navegador.

state.json

Archivo que almacena el último estado conocido de las viviendas.

Contiene información como:

{
  "last_check": "2026-08-31T18:15:31.176545",
  "homes": {
    "bloque-1-vivienda-1": {
      "block": 1,
      "home": 1,
      "floor": "Planta Baja",
      "bedrooms": 2,
      "bathrooms": 2,
      "garage": "48",
      "storage": "22",
      "surface": "64,11",
      "terrace": "21,45",
      "price": 197876.0,
      "status": "available"
    }
  }
}

El archivo permite comparar la información obtenida durante una ejecución con la información de la ejecución anterior.

De esta manera se pueden detectar cambios de estado sin tener que notificar continuamente las mismas viviendas.

Por ejemplo:

available → reserved

indica que una vivienda que estaba disponible ahora aparece como reservada.

También puede detectarse el cambio inverso:

reserved → available

El campo last_check indica cuándo se realizó la última comprobación registrada.

requirements.txt

Contiene las dependencias Python necesarias para ejecutar el proyecto:

requests
beautifulsoup4

Para instalarlas:

pip install -r requirements.txt

.gitignore

Define los archivos y directorios que Git no debe incluir en el repositorio.

Actualmente contiene:

.venv/
__pycache__/
*.py[cod]
.env
.DS_Store

Esto evita subir al repositorio:

* Entornos virtuales de Python.
* Caché de Python.
* Archivos .pyc.
* Archivos .env.
* Archivos propios de macOS.

README.md

Documentación principal del proyecto.

Describe:

* Funcionamiento.
* Arquitectura.
* Ficheros.
* GitHub Actions.
* cron-job.org.
* Configuración.
* Seguridad.
* Sincronización local.

Notificaciones

El proyecto utiliza ntfy para enviar notificaciones.

En web_check.py se define:

NTFY_TOPIC = "sergio-attics-2-2713"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

Cuando se detecta un cambio relevante, el script utiliza este servicio para enviar una notificación.

El dispositivo que esté suscrito al mismo topic puede recibir las notificaciones.

El topic debe considerarse un dato sensible si se utiliza como canal privado de notificaciones. Si se desea mayor privacidad, se recomienda utilizar un topic difícil de adivinar y no publicarlo innecesariamente.

Dependencias

El proyecto utiliza Python 3.

Dependencias:

requests
beautifulsoup4

Para crear un entorno virtual:

python3 -m venv .venv

Activarlo en macOS/Linux:

source .venv/bin/activate

Instalar dependencias:

pip install -r requirements.txt

Ejecutar manualmente el monitor:

python web_check.py

GitHub Actions

El workflow está ubicado en:

.github/workflows/monitor.yml

Actualmente utiliza únicamente:

on:
  workflow_dispatch:

No se utiliza el disparador:

schedule:

La ejecución programada se realiza externamente mediante cron-job.org.

El workflow continúa siendo responsable de ejecutar el código y, cuando corresponde, actualizar el repositorio.

Configuración de cron-job.org

cron-job.org se utiliza como programador externo para iniciar GitHub Actions cada 15 minutos.

1. Crear una cuenta

Acceder a:

https://cron-job.org/

Crear una cuenta e iniciar sesión.

2. Crear un Cronjob

Desde el panel:

Console → Cronjobs → Create cronjob

Crear un nuevo trabajo.

Título recomendado:

Residencial Monitor Trigger

3. Configurar la URL

La URL debe ser:

https://api.github.com/repos/SergioCavilla46/residencial-attics-monitor/actions/workflows/monitor.yml/dispatches

La estructura general es:

https://api.github.com/repos/USUARIO/REPOSITORIO/actions/workflows/WORKFLOW/dispatches

En este proyecto:

USUARIO      = SergioCavilla46
REPOSITORIO  = residencial-attics-monitor
WORKFLOW     = monitor.yml
RAMA         = main

4. Configurar la frecuencia

Seleccionar:

Every 15 minutes

El cronjob solicitará la ejecución del workflow aproximadamente cada 15 minutos.

5. Configurar el método HTTP

Seleccionar:

POST

6. Configurar el Request Body

Utilizar:

{
  "ref": "main"
}

Esto indica a GitHub que el workflow debe ejecutarse sobre la rama main.

7. Configurar los Headers

Añadir:

Authorization: Bearer TU_GITHUB_TOKEN
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2026-03-10

Configuración:

Header	Valor
Authorization	Bearer TU_GITHUB_TOKEN
Accept	application/vnd.github+json
X-GitHub-Api-Version	2026-03-10

TU_GITHUB_TOKEN representa el Personal Access Token de GitHub.

Nunca guardar el token real en este README ni en el repositorio.

Personal Access Token de GitHub

La petición de cron-job.org necesita autenticarse contra GitHub.

Se recomienda utilizar un Fine-grained Personal Access Token.

Ruta:

GitHub
→ Settings
→ Developer settings
→ Personal access tokens
→ Fine-grained tokens

Configurar el acceso para:

Repository access:
Only select repositories

Seleccionar:

residencial-attics-monitor

Y proporcionar el permiso necesario para ejecutar workflows de GitHub Actions:

Actions: Read and write

Una vez generado, copiar el token y almacenarlo de forma segura.

GitHub no volverá a mostrar el token completo después de abandonar la pantalla de creación.

En la documentación se utiliza siempre:

TU_GITHUB_TOKEN

como placeholder.

Nunca sustituir este valor en el README por el token real.

Probar cron-job.org

Después de crear el cronjob:

Test / Run now

Ejecutar una prueba manual.

Después revisar el historial de ejecuciones de cron-job.org.

Comprobar el código HTTP recibido y la respuesta.

Si la petición es aceptada correctamente, GitHub debería iniciar el workflow.

Después comprobar:

GitHub
→ Repository
→ Actions
→ Residencial Aticos Monitor

Debe aparecer una nueva ejecución.

Solución de problemas

Si el workflow no se ejecuta, comprobar:

1. URL de la API
2. Nombre exacto de monitor.yml
3. Rama main
4. Personal Access Token
5. Permisos del token
6. Header Authorization
7. Header Accept
8. Request Body
9. workflow_dispatch
10. Que el workflow esté habilitado

El workflow debe contener:

on:
  workflow_dispatch:

Sin workflow_dispatch, GitHub no podrá iniciar el workflow mediante la API.

Sincronización con GitHub

El repositorio está clonado localmente y utiliza:

origin

como repositorio remoto.

Repositorio:

https://github.com/SergioCavilla46/residencial-attics-monitor.git

Rama principal:

main

Para comprobar el estado:

git status

Para descargar la información más reciente de GitHub:

git fetch origin

Para hacer que la copia local coincida exactamente con GitHub:

git reset --hard origin/main

Después:

git status

Si está sincronizado:

En la rama main
Tu rama está actualizada con 'origin/main'.
nada para hacer commit, el árbol de trabajo está limpio

Subir cambios desde local

Cuando se modifica el proyecto localmente:

git status

Revisar los cambios y añadirlos:

git add .

Crear el commit:

git commit -m "Descripción del cambio"

Subirlo a GitHub:

git push origin main

Comprobar:

git status

Flujo de desarrollo

El flujo habitual para modificar el proyecto es:

             ┌──────────────────┐
             │       Mac        │
             │                  │
             │ Código local     │
             └────────┬─────────┘
                      │
                 git add
                      │
                 git commit
                      │
                 git push
                      │
                      ▼
             ┌──────────────────┐
             │      GitHub      │
             │      main        │
             └──────────────────┘

Para actualizar el código local desde GitHub:

git fetch origin
git reset --hard origin/main

Seguridad

No almacenar en el repositorio:

Personal Access Tokens
Contraseñas
API Keys
Credenciales
Cookies
Tokens privados

El archivo .gitignore excluye .env, por lo que las credenciales locales pueden almacenarse mediante variables de entorno si el proyecto las necesita en el futuro.

Si un token se publica accidentalmente, debe revocarse inmediatamente y generar uno nuevo.

Archivos excluidos

Los siguientes elementos existen en el entorno local pero no deben formar parte del repositorio:

.venv/
__pycache__/
*.pyc

El entorno virtual debe crearse de nuevo en cada máquina cuando sea necesario:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Estado actual del proyecto

Actualmente:

* El repositorio está alojado en GitHub.
* La rama principal es main.
* El repositorio local está sincronizado con origin/main.
* El monitor está implementado en web_check.py.
* state.json almacena el último estado conocido de las viviendas.
* requirements.txt contiene las dependencias Python.
* .gitignore excluye archivos locales y temporales.
* GitHub Actions ejecuta el monitor.
* El workflow está ubicado en .github/workflows/monitor.yml.
* El workflow utiliza workflow_dispatch.
* No se utiliza schedule de GitHub Actions.
* cron-job.org programa la ejecución cada 15 minutos.
* cron-job.org utiliza la API REST de GitHub para iniciar el workflow.
* El monitor consulta la web de la promoción.
* BeautifulSoup procesa el HTML.
* Los cambios de estado se comparan con state.json.
* Las modificaciones relevantes generan una notificación mediante ntfy.
* El estado actualizado puede guardarse en state.json y subirse al repositorio.

Flujo completo

┌──────────────────────────┐
│       cron-job.org       │
│                          │
│     Cada 15 minutos      │
└────────────┬─────────────┘
             │
             │ HTTP POST
             ▼
┌──────────────────────────┐
│       GitHub API         │
│                          │
│   workflow_dispatch      │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│     GitHub Actions       │
│                          │
│      monitor.yml         │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│       web_check.py       │
│                          │
│   Consulta la página     │
│   Extrae las viviendas   │
│   Compara los estados    │
└────────────┬─────────────┘
             │
        ┌────┴────┐
        │         │
        ▼         ▼
┌─────────────┐ ┌─────────────┐
│ state.json  │ │   ntfy.sh   │
│             │ │             │
│ Estado      │ │ Notificación│
│ anterior    │ │ de cambios  │
└─────────────┘ └─────────────┘
             │
             ▼
┌──────────────────────────┐
│        GitHub            │
│                          │
│ Actualización de estado  │
└──────────────────────────┘

Una vez pegado en README.md, desde casa-script haz:

git add README.md
git commit -m "Document project structure and cron configuration"
git push origin main

Y finalmente:

git status

