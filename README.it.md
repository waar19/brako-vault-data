# Dati offline di password violate per Brako Vault

[English](README.md) | [Español](README.es.md) | [Português](README.pt.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | **[Italiano](README.it.md)** | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)**

Questo repository **pubblico** contiene i filtri di Bloom (`.blf`)
che [Brako Vault](https://github.com/waar19/brako-vault) usa per
rilevare le password violate **senza connessione a internet**. Ogni
filtro è derivato dal corpus pubblico Pwned Passwords mantenuto da
Have I Been Pwned, ed è pubblicato come release in modo che la
pipeline di build (CI) di Brako Vault lo scarichi, oppure l'utente
lo importi manualmente.

## Perché un repository separato e pubblico?

L'APK di Brako Vault **non dichiara mai il permesso `INTERNET`**
(vedi il `SECURITY.md` in
[waar19/brako-vault-releases](https://github.com/waar19/brako-vault-releases/blob/master/SECURITY.md)).
Ciò significa che i dati devono viaggiare **dentro** l'APK oppure
essere importati manualmente dall'utente da un file.

Inoltre, l'intero corpus di Pwned Passwords pesa decine di
gigabyte. Generare i filtri richiede un runner con RAM e tempo
generosi. I repository **pubblici** su GitHub hanno minuti di
Actions **gratuiti e illimitati** sui runner standard, mentre
quelli privati sono addebitati sul piano del proprietario. Per
questo questo repository è pubblico e autosufficiente.

## Cosa c'è qui

- **`tools/leaked-password-filter/`** — generatore in Python 3.
  `build_filter.py` trasforma l'output `HASH:COUNT` del corpus in
  un `.blf`. `download_and_build.py` effettua lo streaming degli
  intervalli SHA-1 ufficiali di Pwned Passwords (senza salvare
  l'intero corpus su disco) e costruisce i filtri in parallelo.
  `test_build_filter.py` valida il formato. `measure_fpr.py`
  misura il tasso empirico di falsi positivi.
- **`.github/workflows/build-data.yml`** — workflow manuale
  (`workflow_dispatch`) che esegue il generatore su un runner di
  GitHub Actions e pubblica gli artefatti come release.

## Attribuzione e licenza

Il filtro delle password violate in questo repository è un derivato
in formato Bloom filter del corpus Pwned Passwords, creato e
mantenuto da Have I Been Pwned, un servizio gestito da Troy Hunt.

- **Servizio Pwned Passwords**: <https://haveibeenpwned.com/Passwords>
- **Gestore**: Troy Hunt — <https://www.troyhunt.com>
- **Servizio**: Have I Been Pwned — <https://haveibeenpwned.com>
- **API pubblica usata al momento del build**:
  `https://api.pwnedpasswords.com/range/{prefix}` — vedi
  <https://haveibeenpwned.com/API/v3#PwnedPasswords>
- **Downloader ufficiale di riferimento**:
  <https://github.com/HaveIBeenPwned/PwnedPasswordsDownloader>

L'API di Pwned Passwords è offerta **senza requisiti di licenza né
di attribuzione**. La documentazione ufficiale di Have I Been Pwned
afferma letteralmente: *"In order to help maximise adoption, there
is no licencing or attribution requirements on the Pwned Passwords
API, although it is welcomed if you would like to include it."*
(vedi <https://haveibeenpwned.com/API/v3#PwnedPasswords>). Le API
breach e paste di HIBP sono separatamente sotto licenza CC BY 4.0,
ma **questa licenza non si applica a Pwned Passwords**, e questo
repository non utilizza tali endpoint.

Brako Vault include questa sezione di attribuzione per rendere
esplicita la provenienza dei dati, non perché sia obbligatorio. Se
ridistribuisci i file `.blf` di questo repository, per favore
mantieni intatta questa sezione.

### Cosa contiene questo repository — e cosa no

- Il corpus Pwned Passwords stesso: **no**. Questo repository
  contiene solo un derivato in formato Bloom filter degli hash
  SHA-1.
- Password in chiaro: **no**. Solo i bit del filtro di Bloom.
- Contatto di rete con HIBP **al momento del build**: sì.
  `download_and_build.py` esegue richieste GET verso
  `api.pwnedpasswords.com/range/{prefix}` per scaricare gli
  intervalli SHA-1 in streaming. Lo script non memorizza il
  corpus in locale; elabora ogni intervallo, mantiene un heap dei
  primi N hash e scarta il resto.
- Contatto di rete con HIBP **a runtime nell'app Brako Vault**:
  **no**. L'APK non dichiara il permesso `INTERNET`.

## Formato `.blf`

Ogni file `.blf` è un filtro di Bloom sugli SHA-1 delle password
violate. **Non contiene password in chiaro**, solo i bit del
filtro. L'app client:

1. Calcola lo `SHA-1` della password candidata.
2. Deriva due indici a 64 bit applicando SHA-256 su quei 20 byte
   (schema di doppio hash di Kirsch-Mitzenmacher).
3. Controlla i bit corrispondenti nel `.blf`.

Un risultato positivo del filtro significa "questa password
**potrebbe** essere violata"; l'app la segnala. Il filtro è
dimensionato per mantenere il tasso empirico di falsi positivi a
1 su 10 000 o meno (calibrato e misurato da `measure_fpr.py`).

## Release

Ogni esecuzione riuscita del workflow pubblica una release con il
tag `leaked-passwords-YYYY-MM-DD-N` (data del corpus + numero di
esecuzione) e questi asset:

| File | Dimensione approssimativa | Uso |
|---|---|---|
| `brako-vault-leaked-passwords-base-1m.blf` | ~2-3 MB | Incorporato nell'APK. Copre il milione di password violate più diffuse. |
| `brako-vault-leaked-passwords-base-1m.blf.sha256` | ~100 B | Checksum SHA-256 della base, per verifica in CI. |
| `brako-vault-leaked-passwords-10m.blf` | ~20-30 MB | Pacchetto opzionale da 10 milioni. **Non** entra nell'APK; l'utente lo scarica dalle Impostazioni. |
| `brako-vault-leaked-passwords-10m.blf.sha256` | ~100 B | Checksum SHA-256 del pacchetto, per verifica all'importazione. |

## Come l'app usa questi dati

### Base da 1 milione (incorporata nell'APK)

La CI di [waar19/brako-vault](https://github.com/waar19/brako-vault)
scarica `brako-vault-leaked-passwords-base-1m.blf` dall'ultima
release di questo repository, **verifica il suo SHA-256**, e lo
posiziona in `androidApp/src/main/assets/leaked-passwords/base.blf`
prima della compilazione. Se il checksum non corrisponde, il build
fallisce.

### Pacchetto da 10 milioni (importazione manuale)

L'utente scarica `brako-vault-leaked-passwords-10m.blf` (e il suo
`.sha256`) dalla pagina Releases di questo repository, e dall'app
apre **Impostazioni → Database password violate → Importa
espansione**. L'app apre il selettore file di sistema (SAF),
l'utente sceglie il `.blf` scaricato, e l'app verifica lo SHA-256
prima di attivare la base estesa. Se la verifica fallisce, la base
non viene attivata.

## Come generare una nuova release

1. Vai alla scheda **Actions** di questo repository.
2. Seleziona il workflow **"Build offline breach database"**.
3. Clicca **Run workflow** e inserisci:
   - `corpus_date`: data UTC del corpus da usare (formato
     `YYYY-MM-DD`).
   - `base_limit`: numero di hash nella base incorporata (default
     `1000000`).
   - `expansion_limit`: numero di hash nell'espansione (default
     `10000000`).
4. Attendi. La generazione può richiedere 1-2 ore (è gratuita
   perché il repository è pubblico). Il log mostra l'avanzamento
   per ogni intervallo SHA-1.
5. Alla fine, la release appare nella scheda **Releases** con i
   4 asset.

Per i dettagli tecnici del generatore (schema di
Kirsch-Mitzenmacher, verifica Content-MD5, selezione top-N tramite
heap, modalità bootstrap), vedi
[`tools/leaked-password-filter/README.md`](tools/leaked-password-filter/README.md).

## Verifica locale

Se vuoi provare il generatore senza aspettare il workflow:

```bash
git clone https://github.com/waar19/brako-vault-data.git
cd brako-vault-data
python -m unittest discover -s tools/leaked-password-filter -p "test_*.py"
```

I test usano un piccolo corpus sintetico, non richiedono la rete, e
validano il formato `.blf` e l'API del generatore.

## Privacy

Questo repository non contiene dati personali. Contiene solo bit di
filtri di Bloom derivati da hash SHA-1 pubblici di password
violate. Nessun dato delle utenti e degli utenti di Brako Vault,
nessun indirizzo email, nessun contenuto di breach, nessuna
password in chiaro è qui memorizzato.
