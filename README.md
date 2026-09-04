# Datos offline de contraseñas filtradas para Brako Vault

Este repositorio **público** contiene los filtros de Bloom (`.blf`) que
Brako Vault usa para detectar contraseñas filtradas **sin conexión a
internet**. Se genera a partir del corpus público de Pwned Passwords de
Have I Been Pwned y se publica como release para que Brako Vault lo
descargue en tiempo de build (CI) o el usuario lo importe manualmente.

## ¿Por qué un repositorio separado y público?

La app Brako Vault **jamás declara el permiso `INTERNET`** en su APK
(ver `SECURITY.md` de [waar19/brako-vault](https://github.com/waar19/brako-vault)).
Por eso necesita que los datos viajen **dentro** del APK o que el
usuario los importe a mano desde un archivo.

Además, el corpus de Pwned Passwords pesa decenas de GB. Generar los
filtros requiere un runner con RAM y tiempo generoso. Los repos
**públicos** en GitHub tienen minutos de Actions **gratis e
ilimitados** en runners estándar, mientras que los privados cuentan
contra el plan del dueño. Por eso este repo es público y autocontenido.

## ¿Qué hay aquí?

- **`tools/leaked-password-filter/`** — generador en Python 3.
  `build_filter.py` transforma la salida `HASH:COUNT` del corpus en
  un `.blf`. `download_and_build.py` descarga en streaming los rangos
  SHA-1 oficiales de Pwned Passwords (sin guardar el corpus completo
  a disco) y construye los filtros en paralelo. `test_build_filter.py`
  valida el formato. `measure_fpr.py` mide la tasa de falsos
  positivos.
- **`.github/workflows/build-data.yml`** — workflow manual
  (`workflow_dispatch`) que corre el generador en un runner de
  GitHub Actions y publica los artefactos como release.

## Formato `.blf`

Cada archivo `.blf` es un filtro de Bloom sobre los SHA-1 de las
contraseñas filtradas. **No contiene contraseñas en claro**, solo
los bits del filtro. La app cliente:

1. Calcula `SHA-1` de la contraseña candidata.
2. Deriva dos hashes de 64 bits con SHA-256 sobre esos 20 bytes
   (esquema doble-hash de Kirsch-Mitzenmacher).
3. Comprueba los bits correspondientes en el `.blf`.

Un positivo del filtro significa "la contraseña **podría** estar
filtrada". La app entonces la marca como filtrada. El filtro tiene
una tasa de falsos positivos medida (típicamente ≤ 0,0001) calibrada
en `measure_fpr.py`.

## Releases

Cada ejecución exitosa del workflow publica un release con la
etiqueta `leaked-passwords-YYYY-MM-DD-N` (fecha del corpus + número
de corrida) con estos assets:

| Archivo | Tamaño aproximado | Uso |
|---|---|---|
| `brako-vault-leaked-passwords-base-1m.blf` | ~2-3 MB | Embebido en el APK. Detecta las 1 millón de contraseñas más prevalentes. |
| `brako-vault-leaked-passwords-base-1m.blf.sha256` | ~100 B | Checksum SHA-256 de la base, para verificación en CI. |
| `brako-vault-leaked-passwords-10m.blf` | ~20-30 MB | Paquete opcional de 10 millones. **No** entra en el APK; el usuario lo descarga desde Ajustes. |
| `brako-vault-leaked-passwords-10m.blf.sha256` | ~100 B | Checksum SHA-256 del paquete, para verificación al importar. |

## Cómo se usan desde la app

### Base de 1 millón (embebida en el APK)

El CI de [waar19/brako-vault](https://github.com/waar19/brako-vault)
descarga `brako-vault-leaked-passwords-base-1m.blf` desde el release
más reciente de este repo, **verifica su SHA-256**, y la coloca en
`androidApp/src/main/assets/leaked-passwords/base.blf` antes de
compilar. Si el checksum no coincide, el build falla.

### Paquete de 10 millones (importación manual)

El usuario descarga `brako-vault-leaked-passwords-10m.blf` (y su
`.sha256`) desde la página de releases de este repo, y desde la app
va a **Ajustes → Base de datos de contraseñas filtradas → Importar
expansión**. La app abre el selector de archivos del sistema (SAF),
el usuario elige el `.blf` descargado, y la app verifica el SHA-256
antes de activar la base ampliada. Si la verificación falla, la base
no se activa.

## Atribución

Los datos derivan del corpus **Pwned Passwords** de **Have I Been
Pwned**, de uso libre con atribución:

- <https://haveibeenpwned.com/Passwords>
- Licencia: <https://haveibeenpwned.com/API/v3#License>

Brako Vault no almacena, transmite ni contacta el servicio de HIBP.
Solo embebe y opcionalmente importa un derivado en formato Bloom
filter.

## Cómo generar un release nuevo

1. Ve a la pestaña **Actions** de este repo.
2. Selecciona el workflow **"Build offline breach database"**.
3. Pulsa **Run workflow** e introduce:
   - `corpus_date`: fecha UTC del corpus a usar (formato `YYYY-MM-DD`).
   - `base_limit`: cantidad de hashes en la base embebida (default
     `1000000`).
   - `expansion_limit`: cantidad de hashes en la expansión (default
     `10000000`).
4. Espera. La generación puede tardar 1-2 horas (es gratis por ser
   repo público). El log muestra el progreso de cada rango SHA-1.
5. Al terminar, el release aparece en la pestaña **Releases** con
   los 4 assets.

## Verificación local

Si querés probar el generador sin esperar el workflow:

```bash
git clone https://github.com/waar19/brako-vault-data.git
cd brako-vault-data
python -m unittest discover -s tools/leaked-password-filter -p "test_*.py"
```

Los tests usan un corpus sintético pequeño, no requieren red, y
validan el formato `.blf` y la API del generador.
