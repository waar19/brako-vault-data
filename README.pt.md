# Dados offline de senhas vazadas para o Brako Vault

[English](README.md) | [Español](README.es.md) | **[Português](README.pt.md)** | [Français](README.fr.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

Este repositório **público** contém os filtros de Bloom (`.blf`) que
o [Brako Vault](https://github.com/waar19/brako-vault-releases) usa para
detectar senhas vazadas **sem conexão à internet**. Cada filtro é
derivado do corpus público Pwned Passwords mantido pelo Have I Been
Pwned, e é publicado como release para que o pipeline de build (CI)
do Brako Vault o baixe, ou para que o usuário o importe manualmente.

## Por que um repositório separado e público?

O APK do Brako Vault **nunca declara a permissão `INTERNET`** (veja
o `SECURITY.md` em
[waar19/brako-vault-releases](https://github.com/waar19/brako-vault-releases/blob/master/SECURITY.md)).
Isso significa que os dados precisam viajar **dentro** do APK ou ser
importados manualmente pelo usuário a partir de um arquivo.

Além disso, o corpus completo do Pwned Passwords pesa dezenas de
gigabytes. Gerar os filtros exige um runner com RAM e tempo
generosos. Repositórios **públicos** no GitHub têm minutos de
Actions **grátis e ilimitados** em runners padrão, enquanto os
privados contam contra o plano do dono. Por isso este repositório
é público e autocontido.

## O que está aqui

- **`tools/leaked-password-filter/`** — gerador em Python 3.
  `build_filter.py` transforma a saída `HASH:COUNT` do corpus em um
  `.blf`. `download_and_build.py` faz streaming dos intervalos SHA-1
  oficiais do Pwned Passwords (sem salvar o corpus completo em
  disco) e constrói os filtros em paralelo.
  `test_build_filter.py` valida o formato. `measure_fpr.py` mede a
  taxa empírica de falsos positivos.
- **`.github/workflows/build-data.yml`** — workflow manual
  (`workflow_dispatch`) que executa o gerador em um runner do
  GitHub Actions e publica os artefatos como release.

## Atribuição e licença

O filtro de senhas vazadas deste repositório é um derivado em
formato Bloom filter do corpus Pwned Passwords, criado e mantido
pelo Have I Been Pwned, um serviço operado por Troy Hunt.

- **Serviço Pwned Passwords**: <https://haveibeenpwned.com/Passwords>
- **Operador**: Troy Hunt — <https://www.troyhunt.com>
- **Serviço**: Have I Been Pwned — <https://haveibeenpwned.com>
- **API pública usada no build**:
  `https://api.pwnedpasswords.com/range/{prefix}` — veja
  <https://haveibeenpwned.com/API/v3#PwnedPasswords>
- **Downloader oficial de referência**:
  <https://github.com/HaveIBeenPwned/PwnedPasswordsDownloader>

A API do Pwned Passwords é oferecida **sem requisitos de licença
nem de atribuição**. A documentação oficial do Have I Been Pwned
afirma literalmente: *"In order to help maximise adoption, there is
no licencing or attribution requirements on the Pwned Passwords
API, although it is welcomed if you would like to include it."*
(veja <https://haveibeenpwned.com/API/v3#PwnedPasswords>). As APIs
de breaches e pastes do HIBP são licenciadas separadamente sob CC
BY 4.0, mas **essa licença não se aplica ao Pwned Passwords**, e
este repositório não usa esses endpoints.

O Brako Vault inclui esta seção de atribuição para tornar explícita
a linhagem dos dados, não porque seja obrigatório. Se você
redistribuir os arquivos `.blf` deste repositório, por favor
mantenha esta seção intacta.

### O que este repositório contém — e o que não contém

- O corpus Pwned Passwords em si: **não**. Este repositório contém
  apenas um derivado em formato Bloom filter dos hashes SHA-1.
- Senhas em texto claro: **não**. Apenas os bits do filtro de
  Bloom.
- Contato de rede com o HIBP **em tempo de build**: sim.
  `download_and_build.py` faz requisições GET para
  `api.pwnedpasswords.com/range/{prefix}` para baixar os intervalos
  SHA-1 em streaming. O script não armazena o corpus localmente;
  processa cada intervalo, mantém um heap com os N principais
  hashes e descarta o restante.
- Contato de rede com o HIBP **em tempo de execução no app Brako
  Vault**: **não**. O APK não declara a permissão `INTERNET`.

## Formato `.blf`

Cada arquivo `.blf` é um filtro de Bloom sobre os SHA-1 das senhas
vazadas. **Não contém senhas em texto claro**, apenas os bits do
filtro. O app cliente:

1. Calcula o `SHA-1` da senha candidata.
2. Deriva dois índices de 64 bits aplicando SHA-256 sobre esses 20
   bytes (esquema de double-hash de Kirsch-Mitzenmacher).
3. Verifica os bits correspondentes no `.blf`.

Um resultado positivo do filtro significa "esta senha **pode**
estar vazada"; o app então a sinaliza. O filtro é dimensionado
para manter a taxa empírica de falsos positivos em 1 em 10 000 ou
menos (calibrada e medida por `measure_fpr.py`).

## Releases

Cada execução bem-sucedida do workflow publica um release com a tag
`leaked-passwords-YYYY-MM-DD-N` (rótulo do corpus informado por quem
executa o workflow + número de execução) e estes assets:

| Arquivo | Tamanho aproximado | Uso |
|---|---|---|
| `brako-vault-leaked-passwords-base-1m.blf` | ~2-3 MB | Embutido no APK. Cobre o 1 milhão de senhas vazadas mais prevalentes. |
| `brako-vault-leaked-passwords-base-1m.blf.sha256` | ~100 B | Checksum SHA-256 da base, para verificação independente e no CI. |
| `brako-vault-leaked-passwords-10m.blf` | ~20-30 MB | Pacote opcional de 10 milhões. **Não** vai dentro do APK; o usuário baixa no GitHub Releases e o seleciona em Configurações. |
| `brako-vault-leaked-passwords-10m.blf.sha256` | ~100 B | Checksum SHA-256 do pacote, para verificação independente e no CI. O app não lê este sidecar durante a importação. |

## Como o app usa esses dados

### Base de 1 milhão (embutida no APK)

O workflow privado de publicação do
[Brako Vault](https://github.com/waar19/brako-vault-releases)
baixa os arquivos `.blf` deste repositório e compara cada um com seu
sidecar `.sha256` antes de compilar ou publicar. Ele coloca
`brako-vault-leaked-passwords-base-1m.blf` em
`androidApp/src/main/assets/leaked-passwords/base.blf` antes de
compilar. Se um checksum não bater, o build falha.

### Pacote de 10 milhões (importação manual)

O usuário baixa `brako-vault-leaked-passwords-10m.blf` da página
GitHub Releases deste repositório, abre **Configurações → Base de
senhas vazadas → Importar expansão** e seleciona o `.blf` baixado no
seletor de arquivos do sistema (SAF). O app não lê o sidecar
`.sha256` durante a importação. Em vez disso, valida o digest
SHA-256 interno do corpo do arquivo, armazenado no cabeçalho do
`.blf`, antes de ativar a base ampliada. O sidecar continua
disponível para verificação independente e é usado pelo CI. Se o
digest interno não corresponder, a base não é ativada.

## Como gerar um novo release

1. Vá na aba **Actions** deste repositório.
2. Selecione o workflow **"Build offline breach database"**.
3. Clique em **Run workflow** e informe:
   - `corpus_date`: rótulo `YYYY-MM-DD` informado por quem executa o
     workflow para descrever os dados consultados na API ao vivo do
     Pwned Passwords durante essa execução. Ele não seleciona nem
     fixa um snapshot do corpus.
   - `base_limit`: quantidade configurável de hashes na base embutida
     (default `1000000`).
   - `expansion_limit`: quantidade configurável de hashes na expansão
     (default `10000000`).
   Um release oficial deve usar exatamente `1000000` e `10000000`,
   pois os nomes `base-1m` e `10m` e o app dependem dessas
   quantidades. Os inputs são configuráveis e, por si só, não
   garantem esses valores oficiais.
4. Aguarde. A geração pode levar 1-2 horas (é grátis por o
   repositório ser público). O log mostra o progresso de cada
   intervalo SHA-1.
5. Ao terminar, o release aparece na aba **Releases** com os 4
   assets.

Para detalhes técnicos do gerador (esquema Kirsch-Mitzenmacher,
verificação Content-MD5, seleção top-N por heap, modo bootstrap),
veja [`tools/leaked-password-filter/README.md`](tools/leaked-password-filter/README.md).

## Verificação local

Se você quiser testar o gerador sem esperar pelo workflow:

```bash
git clone https://github.com/waar19/brako-vault-data.git
cd brako-vault-data
python -m unittest discover -s tools/leaked-password-filter -p "test_*.py"
```

Os testes usam um corpus sintético pequeno, não exigem rede, e
validam o formato `.blf` e a API do gerador.

## Privacidade

Este repositório não contém dados pessoais. Contém apenas bits de
filtros de Bloom derivados de hashes SHA-1 públicos de senhas
vazadas. Nenhum dado de usuária ou usuário do Brako Vault, nenhum
endereço de e-mail, nenhum conteúdo de breach, nenhuma senha em
texto claro é armazenado aqui.
