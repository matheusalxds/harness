# manutencao-os

Uma skill do Claude que faz a **manutenção de um segundo cérebro em markdown, qualquer que seja
o formato dele**. Funciona igual num vault de 500 notas com convenção declarada e numa pasta de
notas soltas sem frontmatter nenhum.

O que a torna diferente de um checklist: ela **reconhece a estrutura antes de julgar** e tira a
régua do próprio OS auditado. Um OS de notas planas não é um OS defeituoso, é um OS que escolheu
outra coisa.

## Instalar

Descompacte a pasta em `~/.claude/skills/` e reinicie o Claude Code (ou rode `/reload-plugins`
para carregar na hora):

```bash
unzip manutencao-os.zip -d ~/.claude/skills/
```

Confira que carregou:

```bash
claude plugin list
```

Deve aparecer **`manutencao-os@skills-dir`** com status `loaded`. A pasta traz um manifesto
(`.claude-plugin/plugin.json`), então ela é reconhecida como plugin de verdade: tem versão,
descrição, e dá para ligar e desligar com `claude plugin disable manutencao-os@skills-dir`.

> **Onde NÃO instalar:** dentro da pasta de outro plugin (por exemplo dentro de
> `anthropic-skills/skills/`). Ali ela herda o nome do plugin hospedeiro e passa a se chamar
> `outro-plugin:manutencao-os`, o que quebra a chamada por `/manutencao-os`.

### Para ter `/manutencao-os` no menu de barra

A skill dispara sozinha pela descrição (basta pedir em linguagem natural) e você também pode
digitar `/manutencao-os`. Se quiser que ela **apareça na lista** que abre ao digitar `/`, copie o
comando que vem junto:

```bash
mkdir -p ~/.claude/commands && cp ~/.claude/skills/manutencao-os/extras/manutencao-os.md ~/.claude/commands/
```

Isso vale para o seu usuário inteiro. Para deixar disponível só num projeto, copie para
`.claude/commands/` dentro dele.
## O que ela faz

1. **Reconhece** o OS: roteadores, índices, entidades, uso de frontmatter e de resumo, blocos
   gerados, estado compilado, inbox, rituais, camada de script.
2. **Roda o auditor portátil** (`scripts/audit.py`), que responde em um segundo e a custo zero
   de token tudo que é verificável por comparação: link quebrado, wikilink ambíguo, nota órfã,
   índice incompleto, frase de índice inútil, roteador citando o que não existe, estado
   defasado, captura represada e mais.
3. **Julga o que exige leitura**: fato vencido escrito no presente, contradição entre notas,
   duplicação de verdade, duplicata de conteúdo, deriva de fábrica.
4. **Separa defeito de recomendação.** Defeito é o OS contradizer a si mesmo. Boa prática
   ausente é recomendação, com o custo de não ter, e nunca cobrança.
5. **Corrige só depois de aprovação**, com dry-run numerado e backup.

## A ideia central: régua adaptativa

O auditor não pergunta "este OS segue a boa prática?". Pergunta **"este OS é consistente consigo
mesmo?"**. Na prática:

- **Nota órfã** só é cobrada num OS que de fato usa links.
- **Stub** é medido contra a mediana do próprio OS, não contra um número fixo. Vinte palavras é
  stub num vault de ensaios e é normal num diário.
- **Frontmatter** só é cobrado onde o OS já usa frontmatter na maioria das notas.
- **Estado compilado, índice, blocos gerados**: cada bloco de checks só dispara se o OS tiver
  aquela estrutura.

Se o OS tiver um documento de convenções, **ele vence o script**. Se tiver camada de script
própria, **ela é a autoridade** sobre o que cobre.

## Uso avulso do auditor

O script roda sozinho, sem o Claude, sem configuração e sem dependência fora da biblioteca
padrão do Python:

```bash
python3 scripts/audit.py /caminho/do/os            # relatório legível
python3 scripts/audit.py /caminho/do/os --perfil   # só o reconhecimento
python3 scripts/audit.py /caminho/do/os --json     # para consumo por script
```

Ele **nunca escreve nada**. Diagnóstico que conserta esconde a causa.

## O que tem dentro

```
manutencao-os/
├── .claude-plugin/plugin.json    manifesto: faz a pasta carregar como plugin
├── SKILL.md                      as cinco fases e as regras que não se negociam
├── extras/manutencao-os.md       o comando de barra, para copiar em ~/.claude/commands/
├── references/
│   ├── perfil-do-os.md           como reconhecer a estrutura e derivar a régua
│   ├── checks.md                 o catálogo: o que é script, o que é julgamento, prioridade
│   └── correcao.md               relatório, dry-run, backup, o que nunca automatizar
└── scripts/
    └── audit.py                  o auditor portátil, zero configuração
```

## Companheira

Combina com a skill `os-builder`, que **constrói** um segundo cérebro do zero a partir de uma
entrevista. Esta aqui **mantém** um que já existe, tenha ele sido construído por aquela ou não.
