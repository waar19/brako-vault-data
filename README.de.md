# Offline-Datenbank geleakter Passwörter für Brako Vault

[English](README.md) | [Español](README.es.md) | [Português](README.pt.md) | [Français](README.fr.md) | **[Deutsch](README.de.md)** | [Italiano](README.it.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)**

Dieses **öffentliche** Repository enthält die Bloom-Filter
(`.blf`), die [Brako Vault](https://github.com/waar19/brako-vault)
verwendet, um geleakte Passwörter **ohne Internetverbindung** zu
erkennen. Jeder Filter ist aus dem öffentlichen Pwned-Passwords-Korpus
von Have I Been Pwned abgeleitet und wird als Release veröffentlicht,
sodass die Build-Pipeline (CI) von Brako Vault ihn herunterladen oder
eine Benutzerin oder ein Benutzer ihn manuell importieren kann.

## Warum ein eigenes, öffentliches Repository?

Die Brako-Vault-APK **deklariert niemals die `INTERNET`-Berechtigung**
(siehe `SECURITY.md` in
[waar19/brako-vault-releases](https://github.com/waar19/brako-vault-releases/blob/master/SECURITY.md)).
Das bedeutet, dass die Daten **innerhalb** der APK reisen oder von
der Benutzerin bzw. dem Benutzer manuell aus einer Datei importiert
werden müssen.

Darüber hinaus wiegt der vollständige Pwned-Passwords-Korpus Dutzende
Gigabyte. Das Erzeugen der Filter erfordert einen Runner mit
großzügigem RAM und Zeit. **Öffentliche** GitHub-Repositorys erhalten
auf Standard-Runnern **kostenlose und unbegrenzte** Actions-Minuten,
während private auf den Plan der Besitzerin bzw. des Besitzers
angerechnet werden. Daher ist dieses Repository öffentlich und
in sich geschlossen.

## Was hier ist

- **`tools/leaked-password-filter/`** — Generator in Python 3.
  `build_filter.py` wandelt die `HASH:COUNT`-Ausgabe des Korpus in
  eine `.blf` um. `download_and_build.py` streamt die offiziellen
  SHA-1-Bereiche von Pwned Passwords (ohne den vollständigen
  Korpus auf die Festplatte zu speichern) und baut die Filter
  parallel auf. `test_build_filter.py` validiert das Format.
  `measure_fpr.py` misst die empirische Falsch-Positiv-Rate.
- **`.github/workflows/build-data.yml`** — manueller Workflow
  (`workflow_dispatch`), der den Generator auf einem GitHub-Actions-
  Runner ausführt und die Artefakte als Release veröffentlicht.

## Zuschreibung und Lizenz

Der Geleakte-Passwörter-Filter in diesem Repository ist eine
Bloom-Filter-Ableitung des Pwned-Passwords-Korpus, der von Have I
Been Pwned erstellt und gepflegt wird, einem Dienst, der von Troy
Hunt betrieben wird.

- **Pwned-Passwords-Dienst**: <https://haveibeenpwned.com/Passwords>
- **Betreiber**: Troy Hunt — <https://www.troyhunt.com>
- **Dienst**: Have I Been Pwned — <https://haveibeenpwned.com>
- **Zur Bauzeit verwendete öffentliche API**:
  `https://api.pwnedpasswords.com/range/{prefix}` — siehe
  <https://haveibeenpwned.com/API/v3#PwnedPasswords>
- **Offizielles Downloader-Referenzprojekt**:
  <https://github.com/HaveIBeenPwned/PwnedPasswordsDownloader>

Die Pwned-Passwords-API wird **ohne Lizenz- oder
Zuschreibungsanforderungen** angeboten. Die offizielle
HIBP-Dokumentation stellt wortwörtlich fest: *"In order to help
maximise adoption, there is no licencing or attribution requirements
on the Pwned Passwords API, although it is welcomed if you would
like to include it."* (siehe
<https://haveibeenpwned.com/API/v3#PwnedPasswords>). Die Breach-
und Paste-APIs von HIBP sind separat unter CC BY 4.0 lizenziert,
aber **diese Lizenz gilt nicht für Pwned Passwords**, und dieses
Repository verwendet diese Endpunkte nicht.

Brako Vault enthält diesen Zuschreibungsabschnitt, um die
Datenherkunft explizit zu machen, nicht weil er erforderlich ist.
Wenn Sie die `.blf`-Dateien aus diesem Repository weiterverteilen,
bewahren Sie bitte diesen Abschnitt.

### Was dieses Repository enthält — und was nicht

- Den Pwned-Passwords-Korpus selbst: **nein**. Dieses Repository
  enthält nur eine Bloom-Filter-Ableitung der SHA-1-Hashes.
- Klartext-Passwörter: **nein**. Nur die Bits des Bloom-Filters.
- Netzwerkkontakt mit HIBP **zur Bauzeit**: ja.
  `download_and_build.py` sendet GET-Anfragen an
  `api.pwnedpasswords.com/range/{prefix}`, um SHA-1-Bereiche im
  Streaming herunterzuladen. Das Skript speichert den Korpus nicht
  lokal; es verarbeitet jeden Bereich, behält einen Heap der Top-N
  und verwirft den Rest.
- Netzwerkkontakt mit HIBP **zur Laufzeit in der Brako-Vault-App**:
  **nein**. Die APK deklariert die `INTERNET`-Berechtigung nicht.

## `.blf`-Format

Jede `.blf`-Datei ist ein Bloom-Filter über den SHA-1-Hashes
geleakter Passwörter. **Sie enthält keine Klartext-Passwörter**,
nur die Bits des Filters. Die Client-App:

1. Berechnet `SHA-1` des Kandidaten-Passworts.
2. Leitet zwei 64-Bit-Lane-Indizes ab, indem diese 20 Bytes mit
   SHA-256 gehasht werden (Kirsch-Mitzenmacher-Doppelhaschung).
3. Prüft die entsprechenden Bits in der `.blf`.

Ein positives Ergebnis des Filters bedeutet „dieses Passwort
**könnte** geleakt sein"; die App markiert es dann. Der Filter ist
so dimensioniert, dass die empirische Falsch-Positiv-Rate bei
1 von 10 000 oder darunter liegt (kalibriert und gemessen durch
`measure_fpr.py`).

## Releases

Jede erfolgreiche Ausführung des Workflows veröffentlicht ein
Release mit dem Tag `leaked-passwords-YYYY-MM-DD-N` (Datum des
Korpus + Laufnummer) und diesen Assets:

| Datei | Ungefähre Größe | Verwendung |
|---|---|---|
| `brako-vault-leaked-passwords-base-1m.blf` | ~2-3 MB | In die APK eingebettet. Deckt die 1 Million häufigsten geleakten Passwörter ab. |
| `brako-vault-leaked-passwords-base-1m.blf.sha256` | ~100 B | SHA-256-Prüfsumme der Basis, zur CI-Verifizierung. |
| `brako-vault-leaked-passwords-10m.blf` | ~20-30 MB | Optionales 10-Millionen-Paket. **Wird nicht** in die APK aufgenommen; die Benutzerin/der Benutzer lädt es aus den Einstellungen herunter. |
| `brako-vault-leaked-passwords-10m.blf.sha256` | ~100 B | SHA-256-Prüfsumme des Pakets, zur Verifizierung beim Import. |

## Wie die App diese Daten verwendet

### 1-Million-Basis (in die APK eingebettet)

Die CI von [waar19/brako-vault](https://github.com/waar19/brako-vault)
lädt `brako-vault-leaked-passwords-base-1m.blf` aus dem aktuellsten
Release dieses Repositorys, **verifiziert dessen SHA-256** und legt
es vor dem Kompilieren unter
`androidApp/src/main/assets/leaked-passwords/base.blf` ab. Stimmt
die Prüfsumme nicht, schlägt der Build fehl.

### 10-Millionen-Paket (manueller Import)

Die Benutzerin/der Benutzer lädt
`brako-vault-leaked-passwords-10m.blf` (und seine `.sha256`) von
der Release-Seite dieses Repositorys und öffnet in der App
**Einstellungen → Geleakte-Passwörter-Datenbank → Erweiterung
importieren**. Die App öffnet die System-Dateiauswahl (SAF), die
Benutzerin/der Benutzer wählt die heruntergeladene `.blf`, und
die App verifiziert das SHA-256, bevor sie die erweiterte Basis
aktiviert. Schlägt die Verifizierung fehl, wird die Basis nicht
aktiviert.

## So erzeugen Sie ein neues Release

1. Gehen Sie zum Tab **Actions** dieses Repositorys.
2. Wählen Sie den Workflow **"Build offline breach database"**.
3. Klicken Sie auf **Run workflow** und geben Sie ein:
   - `corpus_date`: UTC-Datum des zu verwendenden Korpus
     (Format `YYYY-MM-DD`).
   - `base_limit`: Anzahl der Hashes in der eingebetteten Basis
     (Standard `1000000`).
   - `expansion_limit`: Anzahl der Hashes in der Erweiterung
     (Standard `10000000`).
4. Warten Sie. Die Erzeugung kann 1-2 Stunden dauern (kostenlos,
   da das Repository öffentlich ist). Das Protokoll zeigt den
   Fortschritt pro SHA-1-Bereich.
5. Danach erscheint das Release im Tab **Releases** mit den
   4 Assets.

Technische Details zum Generator (Kirsch-Mitzenmacher-Schema,
Content-MD5-Verifizierung, Top-N-Auswahl per Heap, Bootstrap-Modus)
finden Sie in
[`tools/leaked-password-filter/README.md`](tools/leaked-password-filter/README.md).

## Lokale Überprüfung

Wenn Sie den Generator ohne den Workflow ausprobieren möchten:

```bash
git clone https://github.com/waar19/brako-vault-data.git
cd brako-vault-data
python -m unittest discover -s tools/leaked-password-filter -p "test_*.py"
```

Die Tests verwenden einen kleinen synthetischen Korpus, benötigen
kein Netzwerk und validieren das `.blf`-Format und die
Generator-API.

## Datenschutz

Dieses Repository enthält keine personenbezogenen Daten. Es
enthält nur Bloom-Filter-Bits, die aus öffentlichen SHA-1-Hashes
geleakter Passwörter abgeleitet sind. Es werden keine Daten von
Brako-Vault-Benutzerinnen oder -Benutzern, keine E-Mail-Adressen,
keine Breach-Inhalte und keine Klartext-Passwörter gespeichert.
