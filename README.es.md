# Datos offline de contraseñas filtradas para Brako Vault

[English](README.md) | **[Español](README.es.md)** | [Português](README.pt.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)**

Este repositorio **público** contiene los filtros de Bloom (`.blf`)
que [Brako Vault](https://github.com/waar19/brako-vault) usa para
detectar contraseñas filtradas **sin conexión a internet**. Cada
filtro es un derivado del corpus público Pwned Passwords mantenido
por Have I Been Pwned, y se publica como release para que el pipeline
de build (CI) de Brako Vault lo descargue, o para que el usuario lo
importe manualmente.

## ¿Por qué un repositorio separado y público?

El APK de Brako Vault **jamás declara el permiso `INTERNET`** (ver
el `SECURITY.md` en
[waar19/brako-vault-releases](https://github.com/waar19/brako-vault-releases/blob/master/SECURITY.md)).
Por eso los datos tienen que viajar **dentro** del APK o ser
importados a mano por el usuario desde un archivo.

Además, el corpus completo de Pwned Passwords pesa decenas de
gigabytes. Generar los filtros requiere un runner con RAM y tiempo
generosos. Los repositorios **públicos** de GitHub tienen minutos
de Actions **gratis e ilimitados** en runners estándar, mientras
que los privados cuentan contra el plan del dueño. Por eso este
repositorio es público y autocontenido.

## ¿Qué hay aquí?

- **`tools/leaked-password-filter/`** — generador en Python 3.
  `build_filter.py` transforma la salida `HASH:COUNT` del corpus en
  un `.blf`. `download_and_build.py` descarga en streaming los
  rangos SHA-1 oficiales de Pwned Passwords (sin guardar el corpus
  completo a disco) y construye los filtros en paralelo.
  `test_build_filter.py` valida el formato. `measure_fpr.py` mide
  la tasa empírica de falsos positivos.
- **`.github/workflows/build-data.yml`** — workflow manual
  (`workflow_dispatch`) que corre el generador en un runner de
  GitHub Actions y publica los artefactos como release.

## Atribución y licencia

El filtro de contraseñas filtradas de este repositorio es un
derivado en formato Bloom filter del corpus Pwned Passwords, creado
y mantenido por Have I Been Pwned, un servicio operado por Troy
Hunt.

- **Servicio Pwned Passwords**: <https://haveibeenpwned.com/Passwords>
- **Operador**: Troy Hunt — <https://www.troyhunt.com>
- **Servicio**: Have I Been Pwned — <https://haveibeenpwned.com>
- **API pública usada en el build**:
  `https://api.pwnedpasswords.com/range/{prefix}` — ver
  <https://haveibeenpwned.com/API/v3#PwnedPasswords>
- **Descargador oficial de referencia**:
  <https://github.com/HaveIBeenPwned/PwnedPasswordsDownloader>

La API de Pwned Passwords se ofrece **sin requisitos de licencia ni
de atribución**. La documentación oficial de Have I Been Pwned dice
textualmente: *"In order to help maximise adoption, there is no
licencing or attribution requirements on the Pwned Passwords API,
although it is welcomed if you would like to include it."* (ver
<https://haveibeenpwned.com/API/v3#PwnedPasswords>). Las APIs de
breaches y pastes de HIBP tienen por separado licencia CC BY 4.0,
pero **esa licencia no se aplica a Pwned Passwords**, y este
repositorio no usa esos endpoints.

Brako Vault incluye esta sección de atribución para hacer explícita
la trazabilidad de los datos, no porque sea obligatoria. Si
redistribuyes los archivos `.blf` de este repositorio, por favor
mantén esta sección intacta.

### Qué contiene este repositorio — y qué no

- El corpus Pwned Passwords mismo: **no**. Este repositorio solo
  contiene un derivado en formato Bloom filter de los hashes SHA-1.
- Contraseñas en claro: **no**. Solo los bits del filtro de Bloom.
- Contacto de red con HIBP **en tiempo de build**: sí.
  `download_and_build.py` hace GET a
  `api.pwnedpasswords.com/range/{prefix}` para descargar rangos
  SHA-1 en streaming. El script no guarda el corpus localmente;
  procesa cada rango, conserva un heap con los N hashes principales
  y descarta el resto.
- Contacto de red con HIBP **en tiempo de ejecución en la app
  Brako Vault**: **no**. El APK no declara el permiso `INTERNET`.

## Formato `.blf`

Cada archivo `.blf` es un filtro de Bloom sobre los SHA-1 de las
contraseñas filtradas. **No contiene contraseñas en claro**, solo
los bits del filtro. La app cliente:

1. Calcula `SHA-1` de la contraseña candidata.
2. Deriva dos índices de 64 bits aplicando SHA-256 sobre esos 20
   bytes (esquema de doble hash de Kirsch-Mitzenmacher).
3. Comprueba los bits correspondientes en el `.blf`.

Un positivo del filtro significa "esta contraseña **podría** estar
filtrada"; la app entonces la marca. El filtro está dimensionado
para mantener la tasa empírica de falsos positivos en 1 de cada
10 000 o menos (calibrada y medida por `measure_fpr.py`).

## Releases

Cada ejecución exitosa del workflow publica un release con la
etiqueta `leaked-passwords-YYYY-MM-DD-N` (fecha del corpus + número
de corrida) y estos assets:

| Archivo | Tamaño aproximado | Uso |
|---|---|---|
| `brako-vault-leaked-passwords-base-1m.blf` | ~2-3 MB | Embebido en el APK. Cubre el 1 millón de contraseñas filtradas más prevalentes. |
| `brako-vault-leaked-passwords-base-1m.blf.sha256` | ~100 B | Checksum SHA-256 de la base, para verificación en CI. |
| `brako-vault-leaked-passwords-10m.blf` | ~20-30 MB | Paquete opcional de 10 millones. **No** entra en el APK; el usuario lo descarga desde Ajustes. |
| `brako-vault-leaked-passwords-10m.blf.sha256` | ~100 B | Checksum SHA-256 del paquete, para verificación al importar. |

## Cómo se usa desde la app

### Base de 1 millón (embebida en el APK)

El CI de [waar19/brako-vault](https://github.com/waar19/brako-vault)
descarga `brako-vault-leaked-passwords-base-1m.blf` desde el release
más reciente de este repositorio, **verifica su SHA-256**, y la
coloca en `androidApp/src/main/assets/leaked-passwords/base.blf`
antes de compilar. Si el checksum no coincide, el build falla.

### Paquete de 10 millones (importación manual)

El usuario descarga `brako-vault-leaked-passwords-10m.blf` (y su
`.sha256`) desde la página de Releases de este repositorio, y desde
la app abre **Ajustes → Base de datos de contraseñas filtradas →
Importar expansión**. La app abre el selector de archivos del
sistema (SAF), el usuario elige el `.blf` descargado, y la app
verifica el SHA-256 antes de activar la base ampliada. Si la
verificación falla, la base no se activa.

## Cómo generar un release nuevo

1. Ve a la pestaña **Actions** de este repositorio.
2. Selecciona el workflow **"Build offline breach database"**.
3. Pulsa **Run workflow** e introduce:
   - `corpus_date`: fecha UTC del corpus a usar (formato
     `YYYY-MM-DD`).
   - `base_limit`: cantidad de hashes en la base embebida (default
     `1000000`).
   - `expansion_limit`: cantidad de hashes en la expansión (default
     `10000000`).
4. Espera. La generación puede tardar 1-2 horas (es gratis por ser
   repositorio público). El log muestra el progreso de cada rango
   SHA-1.
5. Al terminar, el release aparece en la pestaña **Releases** con
   los 4 assets.

Para detalles técnicos del generador (esquema Kirsch-Mitzenmacher,
verificación Content-MD5, selección top-N con heap, modo bootstrap),
ver [`tools/leaked-password-filter/README.md`](tools/leaked-password-filter/README.md).

## Verificación local

Si querés probar el generador sin esperar el workflow:

```bash
git clone https://github.com/waar19/brako-vault-data.git
cd brako-vault-data
python -m unittest discover -s tools/leaked-password-filter -p "test_*.py"
```

Los tests usan un corpus sintético pequeño, no requieren red, y
validan el formato `.blf` y la API del generador.

## Privacidad

Este repositorio no contiene datos personales. Solo contiene bits
de filtros de Bloom derivados de hashes SHA-1 públicos de
contraseñas filtradas. No se almacenan datos de usuarias y usuarios
de Brako Vault, ni direcciones de email, ni contenido de breaches,
ni contraseñas en claro.
