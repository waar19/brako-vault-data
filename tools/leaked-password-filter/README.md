# Generador de filtros de contraseñas filtradas

`build_filter.py` transforma la salida SHA-1 `HASH:COUNT` del descargador oficial
de Pwned Passwords en archivos Bloom `.blf` compatibles con Brako Vault.

## Uso local

```powershell
python tools/leaked-password-filter/build_filter.py C:\datos\pwnedpasswords.txt `
  --corpus-date 2026-09-03 `
  --base-output androidApp/src/main/assets/leaked-passwords/base.blf `
  --base-limit 1000000 `
  --expansion-output dist/brako-vault-leaked-passwords-10m.blf `
  --expansion-limit 10000000
```

También acepta el directorio incremental del descargador. Si cada archivo se
llama con el prefijo SHA-1 de cinco caracteres, el generador reconstruye el hash
completo a partir de cada sufijo.

La selección conserva los hashes de mayor recuento mediante un heap acotado por
`--expansion-limit`. El proceso no guarda contraseñas en claro.

El workflow usa `download_and_build.py`: consulta en paralelo los rangos
oficiales de Pwned Passwords, verifica el `Content-MD5` de cada respuesta y
descarta cada rango después de actualizar el heap. Esto evita guardar en disco
el corpus completo de decenas de GB. Para diez millones de elementos se
recomienda un runner con al menos 8 GiB de RAM.

## Base de arranque

El repositorio incluye una base mínima reproducible generada desde
`bootstrap-hashes.txt`. Solo permite probar de extremo a extremo el formato y la
experiencia antes de incorporar un corpus completo revisado. La interfaz muestra
su cantidad real y no afirma que cubra un millón de hashes.

Para publicar una versión destinada a usuarios se debe ejecutar el workflow
manual con el corpus vigente, revisar sus hashes de artefacto y reemplazar
explícitamente `androidApp/src/main/assets/leaked-passwords/base.blf` por la base
de un millón resultante.

## Verificación de la tasa de falsos positivos

`measure_fpr.py` carga un `.blf` real, verifica su checksum interno y consulta
N contraseñas aleatorias con semilla fija. El script implementa exactamente
la misma función de consulta que el cliente Android
(`LeakedPasswordFilter.mightContainSha1`): SHA-1 del candidato, SHA-256 sobre
esos 20 bytes, dos carriles big-endian combinados con el esquema de doble
hash de Kirsch-Mitzenmacher.

Uso:

```powershell
python tools\leaked-password-filter\measure_fpr.py androidApp\src\main\assets\leaked-passwords\base.blf --samples 50000 --seed 42
```

Salida del artefacto actualmente versionado (base bootstrap de 10 items,
generada el 2026-09-03 desde `bootstrap-hashes.txt`):

```
itemCount=10 bitCount=192 hashCount=13 bodyBytes=24 epochDay=20699
samples=50000 seed=42 positives=0 empiricalFpr=0.000000
```

El criterio de aceptación es FPR medido <= 0,0001; la base bootstrap queda
muy por debajo porque está dimensionada con el mismo objetivo FPR que la base
de producción pero para 10 elementos. Antes de cada release que reemplace
`base.blf` por la base de un millón producida por el workflow, reejecutar la
medición sobre el artefacto final y pegar el resultado en las notas de
release junto al SHA-256 del archivo.
