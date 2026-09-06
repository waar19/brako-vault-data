# Brako Vault 用 オフライン漏洩パスワードデータ

[English](README.md) | [Español](README.es.md) | [Português](README.pt.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | **[日本語](README.ja.md)** | [简体中文](README.zh-CN.md)

この **公開** リポジトリは、
[Brako Vault](https://github.com/waar19/brako-vault-releases) が
**インターネット接続なし** で漏洩パスワードを検出するために使う
Bloom フィルタ (`.blf`) を含みます。各フィルタは Have I Been
Pwned が管理する Pwned Passwords コーパスから派生したもので、
Brako Vault のビルドパイプライン (CI) がダウンロードしたり、
ユーザが手動でインポートしたりできるよう、release として公開
されています。

## なぜ別リポジトリで、しかも公開なのか?

Brako Vault の APK は **決して `INTERNET` 権限を宣言しません**
([waar19/brako-vault-releases](https://github.com/waar19/brako-vault-releases/blob/master/SECURITY.md)
の `SECURITY.md` を参照)。これは、データを APK の **内側** に
持っていくか、ユーザがファイルから手動でインポートする必要が
あるということです。

さらに、Pwned Passwords の完全なコーパスは数十 GB の重さが
あります。フィルタの生成には潤沢な RAM と時間を備えたランナーが
必要です。GitHub の **公開** リポジトリは標準ランナーで
**無料かつ無制限** の Actions 分を使えますが、プライベート
リポジトリではオーナーのプランから消費されます。そのため、
本リポジトリは公開かつ自己完結型となっています。

## 中身

- **`tools/leaked-password-filter/`** — Python 3 製のジェネ
  レータ。`build_filter.py` がコーパスの `HASH:COUNT` 出力を
  `.blf` に変換します。`download_and_build.py` は Pwned
  Passwords の公式 SHA-1 範囲を (コーパス全体をディスクに保存
  せずに) ストリーミングで取得し、フィルタを並列に構築します。
  `test_build_filter.py` がフォーマットを検証し、
  `measure_fpr.py` が経験的な偽陽性率を測定します。
- **`.github/workflows/build-data.yml`** — 手動ワークフロー
  (`workflow_dispatch`)。ジェネレータを GitHub Actions ランナー
  上で実行し、成果物を release として公開します。

## 帰属とライセンス

本リポジトリの漏洩パスワードフィルタは、Pwned Passwords コーパス
の Bloom filter 派生であり、Have I Been Pwned (Troy Hunt が
運営するサービス) が作成・管理しています。

- **Pwned Passwords サービス**: <https://haveibeenpwned.com/Passwords>
- **運営者**: Troy Hunt — <https://www.troyhunt.com>
- **サービス**: Have I Been Pwned — <https://haveibeenpwned.com>
- **ビルド時に使う公開 API**:
  `https://api.pwnedpasswords.com/range/{prefix}` —
  <https://haveibeenpwned.com/API/v3#PwnedPasswords> を参照
- **公式ダウンローダの参照**:
  <https://github.com/HaveIBeenPwned/PwnedPasswordsDownloader>

Pwned Passwords API は **ライセンス要件も帰属要件もなしで**
提供されています。Have I Been Pwned の公式ドキュメントには
次のように明記されています: *"In order to help maximise
adoption, there is no licencing or attribution requirements on
the Pwned Passwords API, although it is welcomed if you would
like to include it."*
(<https://haveibeenpwned.com/API/v3#PwnedPasswords> を参照)。
HIBP の breach API と paste API は別個に CC BY 4.0 の下で
ライセンスされていますが、**このライセンスは Pwned Passwords には
適用されません**。本リポジトリもこれらのエンドポイントは使用
していません。

Brako Vault はデータの系譜を明確にするため、必須ではないものの
この帰属セクションを含めています。本リポジトリの `.blf` ファイル
を再配布する場合は、本セクションをそのまま残してください。

### 本リポジトリが含むもの — 含まないもの

- Pwned Passwords コーパス本体: **含まない**。本リポジトリには
  SHA-1 ハッシュの Bloom filter 派生のみが含まれます。
- 平文パスワード: **含まない**。Bloom フィルタのビットのみ。
- **ビルド時** の HIBP とのネットワーク通信: **あり**。
  `download_and_build.py` は
  `api.pwnedpasswords.com/range/{prefix}` に GET を発行し、
  SHA-1 範囲をストリーミングで取得します。スクリプトはコーパス
  をローカルに保存せず、各範囲を処理して上位 N 件のヒープを
  保持し、残りは破棄します。
- **Brako Vault アプリの実行時** の HIBP とのネットワーク通信:
  **なし**。APK は `INTERNET` 権限を宣言しません。

## `.blf` フォーマット

各 `.blf` ファイルは漏洩パスワードの SHA-1 に対する Bloom フィルタ
です。**平文のパスワードは含まれず**、フィルタのビットだけが
含まれます。クライアントアプリ:

1. 候補パスワードの `SHA-1` を計算する。
2. その 20 バイトに SHA-256 を適用して 64 ビット レーン
   インデックスを 2 つ導く (Kirsch-Mitzenmacher のダブルハッシュ
   スキーム)。
3. `.blf` の対応するビットを確認する。

フィルタの陽性は「このパスワードは **漏洩している可能性が
ある**」ことを意味し、アプリはそれをフラグします。フィルタは
経験的偽陽性率が 10 000 分の 1 以下になるようにサイズ設計されて
います (`measure_fpr.py` で校正・測定)。

## リリース

ワークフローの正常終了ごとに、実行者が指定したコーパスラベルと
連番を含む `leaked-passwords-YYYY-MM-DD-N` タグで次のアセットを
release として公開します:

| ファイル | おおよそのサイズ | 用途 |
|---|---|---|
| `brako-vault-leaked-passwords-base-1m.blf` | 約 2〜3 MB | APK に同梱。最も出現頻度の高い 100 万件の漏洩パスワードをカバー。 |
| `brako-vault-leaked-passwords-base-1m.blf.sha256` | 約 100 B | ベースの SHA-256 チェックサム (独立検証および CI 検証用)。 |
| `brako-vault-leaked-passwords-10m.blf` | 約 20〜30 MB | 任意の 1 千万件パッケージ。APK には **入らない**。ユーザが GitHub Releases からダウンロードし、設定で選択。 |
| `brako-vault-leaked-passwords-10m.blf.sha256` | 約 100 B | パッケージの SHA-256 チェックサム (独立検証および CI 検証用)。アプリはインポート時にこの sidecar を読みません。 |

## アプリでの利用方法

### 100 万件のベース (APK に同梱)

[Brako Vault](https://github.com/waar19/brako-vault-releases) の
非公開リリースワークフローは、本リポジトリから `.blf` ファイルを
ダウンロードし、コンパイルまたは公開の前に各ファイルを対応する
`.sha256` sidecar と照合します。また、ビルド前に
`brako-vault-leaked-passwords-base-1m.blf` を
`androidApp/src/main/assets/leaked-passwords/base.blf` に配置
します。チェックサムが一致しなければビルドは失敗します。

### 1 千万件のパッケージ (手動インポート)

ユーザは本リポジトリの GitHub Releases ページから
`brako-vault-leaked-passwords-10m.blf` をダウンロードし、
アプリ内で **設定 → 漏洩パスワード DB → 拡張をインポート** を
開いて、システムのファイル選択 (SAF) でダウンロードした `.blf`
を選びます。アプリはインポート時に `.sha256` sidecar を読み
ません。代わりに、拡張ベースを有効化する前に `.blf` ヘッダに
格納されたファイル本体の内部 SHA-256 ダイジェストを検証します。
sidecar は独立検証に利用でき、CI でも使用されます。内部
ダイジェストが一致しなければ、ベースは有効化されません。

## 新しい release の生成方法

1. 本リポジトリの **Actions** タブを開く。
2. ワークフロー **"Build offline breach database"** を選択する。
3. **Run workflow** をクリックし、以下を入力する:
   - `corpus_date`: 実行者が指定する `YYYY-MM-DD` ラベル。
     その実行中に Pwned Passwords の live API から取得した
     データを表します。コーパスの snapshot を選択または固定
     するものではありません。
   - `base_limit`: 同梱ベース内の設定可能なハッシュ数
     (デフォルト `1000000`)。
   - `expansion_limit`: 拡張内の設定可能なハッシュ数
     (デフォルト `10000000`)。
   公式 release では、`base-1m` と `10m` というファイル名および
   アプリがこれらの件数に依存するため、正確に `1000000` と
   `10000000` を使用する必要があります。入力値は設定可能であり、
   それ自体が公式値を保証するものではありません。
4. 待機する。生成には 1〜2 時間かかることがある (公開リポ
   なので無料)。ログに各 SHA-1 範囲の進捗が表示される。
5. 完了後、release は **Releases** タブに 4 アセットとともに
   現れる。

ジェネレータの技術的詳細 (Kirsch-Mitzenmacher スキーム、
Content-MD5 検証、ヒープによる top-N 抽出、bootstrap モード)
については、
[`tools/leaked-password-filter/README.md`](tools/leaked-password-filter/README.md)
を参照。

## ローカル検証

ワークフローを待たずにジェネレータを試したい場合:

```bash
git clone https://github.com/waar19/brako-vault-data.git
cd brako-vault-data
python -m unittest discover -s tools/leaked-password-filter -p "test_*.py"
```

テストは小さな合成コーパスを使い、ネットワークを必要とせず、
`.blf` のフォーマットとジェネレータ API を検証します。

## プライバシー

本リポジトリには個人データは一切含まれません。公開されている
漏洩パスワードの SHA-1 ハッシュから派生した Bloom フィルタの
ビットのみが含まれます。Brako Vault のユーザのデータ、email
アドレス、breach 内容、平文パスワードは一切保存されません。
