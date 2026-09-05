# Données hors ligne de mots de passe fuités pour Brako Vault

[English](README.md) | [Español](README.es.md) | [Português](README.pt.md) | **[Français](README.fr.md)** | [Deutsch](README.de.md) | [Italiano](README.it.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)**

Ce dépôt **public** contient les filtres de Bloom (`.blf`) que
[Brako Vault](https://github.com/waar19/brako-vault) utilise pour
détecter les mots de passe fuités **sans connexion internet**. Chaque
filtre est dérivé du corpus public Pwned Passwords maintenu par Have
I Been Pwned, et est publié sous forme de release pour que le
pipeline de build (CI) de Brako Vault le récupère, ou pour que
l'utilisateur l'importe manuellement.

## Pourquoi un dépôt séparé et public ?

L'APK de Brako Vault **ne déclare jamais la permission `INTERNET`**
(voir le `SECURITY.md` dans
[waar19/brako-vault-releases](https://github.com/waar19/brako-vault-releases/blob/master/SECURITY.md)).
Cela signifie que les données doivent voyager **à l'intérieur** de
l'APK ou être importées manuellement par l'utilisateur depuis un
fichier.

De plus, le corpus complet de Pwned Passwords pèse des dizaines de
gigaoctets. La génération des filtres exige un runner avec beaucoup
de RAM et de temps. Les dépôts **publics** de GitHub disposent de
minutes d'Actions **gratuites et illimitées** sur les runners
standard, tandis que les privés sont comptés sur le plan du
propriétaire. C'est pourquoi ce dépôt est public et autonome.

## Ce qu'on trouve ici

- **`tools/leaked-password-filter/`** — générateur en Python 3.
  `build_filter.py` transforme la sortie `HASH:COUNT` du corpus en
  un `.blf`. `download_and_build.py` streame les plages SHA-1
  officielles de Pwned Passwords (sans enregistrer le corpus
  complet sur disque) et construit les filtres en parallèle.
  `test_build_filter.py` valide le format. `measure_fpr.py` mesure
  le taux empirique de faux positifs.
- **`.github/workflows/build-data.yml`** — workflow manuel
  (`workflow_dispatch`) qui exécute le générateur sur un runner
  GitHub Actions et publie les artéfacts en release.

## Attribution et licence

Le filtre de mots de passe fuités de ce dépôt est un dérivé en
format Bloom filter du corpus Pwned Passwords, créé et maintenu par
Have I Been Pwned, un service exploité par Troy Hunt.

- **Service Pwned Passwords** : <https://haveibeenpwned.com/Passwords>
- **Exploitant** : Troy Hunt — <https://www.troyhunt.com>
- **Service** : Have I Been Pwned — <https://haveibeenpwned.com>
- **API publique utilisée au build** :
  `https://api.pwnedpasswords.com/range/{prefix}` — voir
  <https://haveibeenpwned.com/API/v3#PwnedPasswords>
- **Téléchargeur officiel de référence** :
  <https://github.com/HaveIBeenPwned/PwnedPasswordsDownloader>

L'API Pwned Passwords est fournie **sans exigence de licence ni
d'attribution**. La documentation officielle de Have I Been Pwned
indique littéralement : *"In order to help maximise adoption, there
is no licencing or attribution requirements on the Pwned Passwords
API, although it is welcomed if you would like to include it."*
(voir <https://haveibeenpwned.com/API/v3#PwnedPasswords>). Les API
breach et paste de HIBP sont séparément sous licence CC BY 4.0,
mais **cette licence ne s'applique pas à Pwned Passwords**, et ce
dépôt n'utilise pas ces endpoints.

Brako Vault inclut cette section d'attribution pour rendre
explicite la lignée des données, pas parce que c'est obligatoire.
Si vous redistribuez les fichiers `.blf` de ce dépôt, veuillez
conserver cette section intacte.

### Ce que ce dépôt contient — et ce qu'il ne contient pas

- Le corpus Pwned Passwords lui-même : **non**. Ce dépôt contient
  uniquement un dérivé en format Bloom filter des hachés SHA-1.
- Mots de passe en clair : **non**. Seulement les bits du filtre
  de Bloom.
- Contact réseau avec HIBP **au moment du build** : oui.
  `download_and_build.py` envoie des requêtes GET vers
  `api.pwnedpasswords.com/range/{prefix}` pour télécharger les
  plages SHA-1 en streaming. Le script ne stocke pas le corpus en
  local ; il traite chaque plage, garde un tas (heap) des N
  principaux hachés et jette le reste.
- Contact réseau avec HIBP **à l'exécution dans l'application
  Brako Vault** : **non**. L'APK ne déclare pas la permission
  `INTERNET`.

## Format `.blf`

Chaque fichier `.blf` est un filtre de Bloom sur les SHA-1 des mots
de passe fuités. **Il ne contient pas de mots de passe en clair**,
seulement les bits du filtre. L'application cliente :

1. Calcule le `SHA-1` du mot de passe candidat.
2. Dérive deux indices de 64 bits en appliquant SHA-256 sur ces 20
   octets (schéma de double hachage de Kirsch-Mitzenmacher).
3. Vérifie les bits correspondants dans le `.blf`.

Un résultat positif du filtre signifie « ce mot de passe **peut**
être fuit » ; l'application le signale alors. Le filtre est
dimensionné pour maintenir le taux empirique de faux positifs à 1
sur 10 000 ou moins (calibré et mesuré par `measure_fpr.py`).

## Releases

Chaque exécution réussie du workflow publie une release avec le
tag `leaked-passwords-YYYY-MM-DD-N` (date du corpus + numéro
d'exécution) et ces assets :

| Fichier | Taille approximative | Usage |
|---|---|---|
| `brako-vault-leaked-passwords-base-1m.blf` | ~2-3 MB | Intégré dans l'APK. Couvre le million de mots de passe fuités les plus fréquents. |
| `brako-vault-leaked-passwords-base-1m.blf.sha256` | ~100 B | Somme de contrôle SHA-256 de la base, pour vérification CI. |
| `brako-vault-leaked-passwords-10m.blf` | ~20-30 MB | Pack optionnel de 10 millions. **N'entre pas** dans l'APK ; l'utilisateur le télécharge depuis Paramètres. |
| `brako-vault-leaked-passwords-10m.blf.sha256` | ~100 B | Somme de contrôle SHA-256 du pack, pour vérification à l'import. |

## Comment l'application utilise ces données

### Base d'un million (intégrée à l'APK)

La CI de [waar19/brako-vault](https://github.com/waar19/brako-vault)
télécharge `brako-vault-leaked-passwords-base-1m.blf` depuis la
dernière release de ce dépôt, **vérifie son SHA-256**, et la place
dans `androidApp/src/main/assets/leaked-passwords/base.blf` avant la
compilation. Si la somme de contrôle ne correspond pas, le build
échoue.

### Pack de 10 millions (importation manuelle)

L'utilisateur télécharge `brako-vault-leaked-passwords-10m.blf` (et
son `.sha256`) depuis la page Releases de ce dépôt, et depuis
l'application ouvre **Paramètres → Base de mots de passe fuités →
Importer l'extension**. L'application ouvre le sélecteur de
fichiers du système (SAF), l'utilisateur choisit le `.blf`
téléchargé, et l'application vérifie le SHA-256 avant d'activer la
base étendue. Si la vérification échoue, la base n'est pas activée.

## Comment générer une nouvelle release

1. Allez dans l'onglet **Actions** de ce dépôt.
2. Sélectionnez le workflow **"Build offline breach database"**.
3. Cliquez sur **Run workflow** et saisissez :
   - `corpus_date` : date UTC du corpus à utiliser (format
     `YYYY-MM-DD`).
   - `base_limit` : nombre de hachés dans la base intégrée (défaut
     `1000000`).
   - `expansion_limit` : nombre de hachés dans l'extension (défaut
     `10000000`).
4. Patientez. La génération peut prendre 1 à 2 heures (gratuite
   parce que le dépôt est public). Le journal montre la progression
   par plage SHA-1.
5. À la fin, la release apparaît dans l'onglet **Releases** avec
   les 4 assets.

Pour les détails techniques du générateur (schéma de
Kirsch-Mitzenmacher, vérification Content-MD5, sélection top-N par
tas, mode bootstrap), voir
[`tools/leaked-password-filter/README.md`](tools/leaked-password-filter/README.md).

## Vérification locale

Si vous voulez essayer le générateur sans attendre le workflow :

```bash
git clone https://github.com/waar19/brako-vault-data.git
cd brako-vault-data
python -m unittest discover -s tools/leaked-password-filter -p "test_*.py"
```

Les tests utilisent un petit corpus synthétique, ne nécessitent pas
le réseau, et valident le format `.blf` et l'API du générateur.

## Confidentialité

Ce dépôt ne contient aucune donnée personnelle. Il ne contient
que des bits de filtres de Bloom dérivés de hachés SHA-1 publics
de mots de passe fuités. Aucune donnée d'utilisatrice ou
d'utilisateur de Brako Vault, aucune adresse e-mail, aucun contenu
de breach, aucun mot de passe en clair n'est stocké ici.
