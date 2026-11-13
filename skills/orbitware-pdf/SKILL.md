---
name: orbitware-pdf
description: Gera PDFs com a identidade visual da Orbitware Computing Solutions (empresa do Matheus) - orçamento, proposta comercial, relatório, documento de escopo. Use quando o usuário pedir um PDF, orçamento, proposta ou documento da Orbitware, ou de um side project emitido pela Orbitware (ex. Radar Governamental). Não use para material da House Numbers (essa tem a skill slides).
argument-hint: "[tipo de documento e assunto]"
---

# Orbitware PDF

Todo documento sai como HTML com o CSS da marca e vira PDF pelo Chrome headless. Nada de
reestilizar: a identidade está em `assets/orbitware.css`.

## Arquivos
- `assets/orbitware.css`: tokens de cor, tipografia e componentes (`ow-*`). Fonte única do visual.
- `assets/logo.png`: logo (anel prata e azul sobre fundo preto, recorte quadrado).
- `assets/empresa.md`: dados da empresa. Ler antes de montar o cabeçalho e o bloco "Emitente".
- `templates/orcamento.html`: orçamento / proposta comercial. Ponto de partida para os outros tipos.
- `scripts/render.py`: injeta CSS e logo no HTML e gera o PDF.

## Fluxo
1. **Levantar o conteúdo.** Cliente, itens, valores, prazos, condições. O que o usuário não
   informou e não está no contexto: pergunte em uma rodada só. Nunca invente valor, CNPJ, prazo
   ou condição. Dado opcional ausente: remova a linha do template.
2. **Montar o HTML** copiando o template para a pasta de trabalho (no Brainiac:
   `projetos/{Nome}/outputs/`; fora dele, a pasta atual). Manter `{{CSS}}` e `{{LOGO}}` intactos:
   o script substitui. Trocar todos os `[...]`.
3. **Gerar:** `python3 ~/.claude/skills/orbitware-pdf/scripts/render.py arquivo.html [saida.pdf]`.
   O script avisa se sobrou placeholder.
4. **Conferir visualmente** antes de entregar, todas as páginas:
   `swift ~/.claude/skills/orbitware-pdf/scripts/preview.swift saida.pdf [pasta]` gera um PNG por
   página; ler cada um. Procurar quebra de tabela feia, texto estourando, placeholder.
5. Entregar o caminho do PDF. Envio para cliente é sempre do usuário.

## Identidade visual (obrigatória)

Cores extraídas do logo original, guardado em `~/Brainiac/marca/orbitware/orbitware-logo.png`
(anel prata e azul sobre preto). O `assets/logo.png` é um recorte dele; o README da pasta da
marca tem o comando para regenerar.

| Token | Hex | Uso |
|---|---|---|
| `--black` | `#000000` | Faixa do cabeçalho (o fundo do logo some nela), cabeçalho de tabela, caixa do total |
| `--ink` | `#0b0f1f` | Texto principal |
| `--blue` | `#0665f9` | Acento principal: sublinhado de `h2`, rótulos, `<em>` nos títulos |
| `--cyan` | `#25ddfd` | Só sobre preto: tipo do documento e valor total |
| `--accent-bar` | `#0665f9` a `#25ddfd` | Gradiente do filete sob o cabeçalho e dos marcadores de lista |
| `--navy` / `--indigo` | `#01236d` / `#1943a7` | Gráficos e badges |
| `--lavender` / `--silver` | `#b4c3ed` / `#9aa3c4` | Texto secundário sobre preto, linhas de assinatura |
| `--mist` | `#f4f6fd` | Fundo de cards e linhas alternadas da tabela |

Regras:
- **Papel branco no corpo, preto só em faixas.** Documento de negócio é impresso e lido: fundo
  escuro na página inteira gasta tinta e cansa. Capa inteira escura só se o usuário pedir.
- Azul elétrico domina no papel; ciano só aparece sobre preto (no branco ele some).
- Tipografia: `--sans` (Avenir Next) para tudo; `--mono` para rótulos (`ow-eyebrow`), números de
  tabela e datas. Uma palavra-chave por título em `<em>` (fica azul).
- Valores monetários: `R$ 1.234,56`, alinhados à direita em `td.num`.
- Sem travessão (em dash) no texto. Sem buzzword.

## Componentes
`ow-cover` (cabeçalho com logo e meta do documento) · `ow-eyebrow` · `ow-lead` · `ow-parties` +
`ow-card` (emitente e cliente; `.ow-card-logo` + `<img>` como último filho põe o símbolo do cliente, em data URI, à direita e centralizado) · `ow-list` · `ow-table` (com `.num`) · `ow-totals` (`.row`, `.grand`)
· `ow-timeline` + `ow-step` · `ow-callout` · `ow-badge` (`blue`, `cyan`, `navy`, `silver`) ·
`ow-signatures` · `ow-footnote` · `page-break`.

Rodapé (razão social + CNPJ + `página / total`) vem do `@page` do CSS, não precisa de HTML.
O CNPJ já está fixo no template e no rodapé: não pedir de novo. E-mail e telefone entram no
card "Emitente" quando estiverem preenchidos em `assets/empresa.md`.

## Outros tipos de documento
Partir do `orcamento.html`, manter `ow-cover` e trocar o `ow-doc-type` (Proposta, Relatório,
Escopo, Contrato). Seções novas usam os mesmos componentes; se faltar um componente, ele entra
no `orbitware.css`, não inline no documento.
