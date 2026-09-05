# Offline leaked-password data for Brako Vault

**[English](README.md)** | [Español](README.es.md) | [Português](README.pt.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)**

This public repository contains the Bloom filters (`.blf`) that
[Brako Vault](https://github.com/waar19/brako-vault) uses to detect
leaked passwords **without an internet connection**. Each filter is
derived from the public Pwned Passwords corpus maintained by Have I
Been Pwned, and is published as a release so Brako Vault's build
pipeline (CI) can fetch it or a user can import it manually.

## Why a separate, public repository?

The Brako Vault APK **never declares the `INTERNET` permission** (see
the `SECURITY.md` in [waar19/brako-vault-releases](https://github.com/waar19/brako-vault-releases/blob/master/SECURITY.md)).
That means the leaked-password data must travel **inside** the APK or
be imported manually by the user from a file.

In addition, the full Pwned Passwords corpus weighs dozens of
gigabytes. Building the filters requires a runner with generous RAM
and time. **Public** GitHub repositories get unlimited free Actions
minutes on standard runners, while private repositories count against
the owner's plan. That is why this repository is public and
self-contained.

## What is here

- **`tools/leaked-password-filter/`** — Python 3 generator.
  `build_filter.py` transforms the `HASH:COUNT` output of the Pwned
  Passwords corpus into a `.blf` file. `download_and_build.py`
  streams the official SHA-1 ranges from Pwned Passwords (without
  saving the full corpus to disk) and builds the filters in
  parallel. `test_build_filter.py` validates the format.
  `measure_fpr.py` measures the empirical false-positive rate.
- **`.github/workflows/build-data.yml`** — manual workflow
  (`workflow_dispatch`) that runs the generator on a GitHub Actions
  runner and publishes the artifacts as a release.

## Attribution and license

The leaked-password filter in this repository is a Bloom-filter
derivative of the Pwned Passwords corpus, which is created and
maintained by Have I Been Pwned, a service operated by Troy Hunt.

- **Pwned Passwords service**: <https://haveibeenpwned.com/Passwords>
- **Operator**: Troy Hunt — <https://www.troyhunt.com>
- **Service**: Have I Been Pwned — <https://haveibeenpwned.com>
- **Public API used at build time**:
  `https://api.pwnedpasswords.com/range/{prefix}` — see
  <https://haveibeenpwned.com/API/v3#PwnedPasswords>
- **Official downloader reference**:
  <https://github.com/HaveIBeenPwned/PwnedPasswordsDownloader>

The Pwned Passwords API is offered with **no licensing or attribution
requirements**. The official Have I Been Pwned documentation states
literally: *"In order to help maximise adoption, there is no
licencing or attribution requirements on the Pwned Passwords API,
although it is welcomed if you would like to include it."* (see
<https://haveibeenpwned.com/API/v3#PwnedPasswords>). The HIBP
breach/paste APIs are separately licensed under CC BY 4.0, but
**that license does not apply to Pwned Passwords**, and this
repository does not use those endpoints.

Brako Vault includes this attribution section to make the data
lineage explicit, not because it is required. If you redistribute
the `.blf` files from this repository, please keep this section
intact.

### What this repository contains — and what it does not

- The Pwned Passwords corpus itself: **no**. This repository only
  contains a Bloom-filter derivative of the SHA-1 hashes.
- Plaintext passwords: **no**. Only the bits of the Bloom filter.
- Network contact with HIBP **at build time**: yes.
  `download_and_build.py` issues GET requests to
  `api.pwnedpasswords.com/range/{prefix}` to download SHA-1 ranges
  in streaming fashion. The script does not store the corpus
  locally; it processes each range, keeps a heap of the top N
  hashes, and discards the rest.
- Network contact with HIBP **at runtime in the Brako Vault app**:
  **no**. The APK does not declare the `INTERNET` permission.

## `.blf` format

Each `.blf` file is a Bloom filter over the SHA-1 hashes of leaked
passwords. **It does not contain plaintext passwords**, only the bits
of the filter. The client app:

1. Computes `SHA-1` of the candidate password.
2. Derives two 64-bit lane indices by hashing those 20 bytes with
   SHA-256 (Kirsch-Mitzenmacher double-hashing scheme).
3. Checks the corresponding bits in the `.blf`.

A positive result from the filter means "this password **may** be
leaked"; the app then flags it. The filter is sized to keep the
empirical false-positive rate at or below 1 in 10 000
(calibrated and measured by `measure_fpr.py`).

## Releases

Each successful run of the workflow publishes a release with the tag
`leaked-passwords-YYYY-MM-DD-N` (corpus date + run number) and these
assets:

| File | Approximate size | Use |
|------|------------------|-----|
| `brako-vault-leaked-passwords-base-1m.blf` | ~2-3 MB | Embedded in the APK. Covers the 1 million most prevalent leaked passwords. |
| `brako-vault-leaked-passwords-base-1m.blf.sha256` | ~100 B | SHA-256 checksum of the base, for CI verification. |
| `brako-vault-leaked-passwords-10m.blf` | ~20-30 MB | Optional 10-million package. **Does not** ship inside the APK; the user downloads it from Settings. |
| `brako-vault-leaked-passwords-10m.blf.sha256` | ~100 B | SHA-256 checksum of the package, for verification on import. |

## How the app uses this data

### 1-million base (embedded in the APK)

The CI of [waar19/brako-vault](https://github.com/waar19/brako-vault)
downloads `brako-vault-leaked-passwords-base-1m.blf` from the latest
release of this repository, **verifies its SHA-256**, and places it in
`androidApp/src/main/assets/leaked-passwords/base.blf` before
compiling. If the checksum does not match, the build fails.

### 10-million package (manual import)

The user downloads `brako-vault-leaked-passwords-10m.blf` (and its
`.sha256`) from the Releases page of this repository, and from the
app opens **Settings → Leaked-password database → Import expansion**.
The app opens the system file picker (SAF), the user selects the
downloaded `.blf`, and the app verifies the SHA-256 before activating
the expanded base. If the verification fails, the base is not
activated.

## How to generate a new release

1. Go to the **Actions** tab of this repository.
2. Select the workflow **"Build offline breach database"**.
3. Click **Run workflow** and enter:
   - `corpus_date`: UTC date of the corpus to use
     (`YYYY-MM-DD` format).
   - `base_limit`: number of hashes in the embedded base
     (default `1000000`).
   - `expansion_limit`: number of hashes in the expansion
     (default `10000000`).
4. Wait. Generation can take 1-2 hours (free, because the repository
   is public). The log shows progress per SHA-1 range.
5. When finished, the release appears in the **Releases** tab with
   the 4 assets.

For technical details of the generator (Kirsch-Mitzenmacher scheme,
Content-MD5 verification, heap-based top-N selection, bootstrap
mode), see
[`tools/leaked-password-filter/README.md`](tools/leaked-password-filter/README.md).

## Local verification

If you want to try the generator without waiting for the workflow:

```bash
git clone https://github.com/waar19/brako-vault-data.git
cd brako-vault-data
python -m unittest discover -s tools/leaked-password-filter -p "test_*.py"
```

The tests use a small synthetic corpus, do not require the network,
and validate the `.blf` format and the generator API.

## Privacy

This repository does not contain any personal data. It contains only
Bloom-filter bits derived from public SHA-1 hashes of leaked
passwords. No Brako Vault user data, no email addresses, no breach
content, and no plaintext passwords are stored here.
