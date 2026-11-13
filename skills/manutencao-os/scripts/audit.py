#!/usr/bin/env python3
"""audit.py: auditor portatil de OS em markdown. Zero configuracao.

Descobre a estrutura do OS antes de julgar, e deriva a regua do PROPRIO OS: so cobra
uma convencao que aquele OS ja segue na maioria dos casos. Um OS de notas planas sem
frontmatter nao e um OS defeituoso, e um OS que escolheu outra coisa.

    python3 audit.py [raiz]            relatorio legivel
    python3 audit.py [raiz] --json     para consumo por script
    python3 audit.py [raiz] --perfil   so o reconhecimento, sem achados

Nao escreve nada, nunca. Diagnostico que conserta esconde a causa.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import unquote

IGNORE = {".git", ".tmp", "tmp", ".obsidian", "node_modules", "__pycache__",
          ".venv", "venv", ".trash", ".DS_Store", "_arquivados", "_archive", "archive"}
ROTEADOR = {"CLAUDE.md", "SKILL.md", "AGENTS.md", "README.md", "COMO-USAR.md", "HOW-TO-USE.md"}
CONVENCAO = {"CONVENCOES.md", "CONVENTIONS.md", "CONVENCOES.MD"}
CAMPOS_RESUMO = ("resumo", "summary", "description", "descricao", "abstract")
CAMPOS_DATA_REV = ("atualizado", "updated", "revisado", "last_updated")
NOMES_INBOX = {"inbox", "capture", "capturas", "00-inbox", "_inbox", "caixa-de-entrada"}
RE_AUTO = re.compile(r"<!--\s*AUTO:([\w-]+)\s*-->(.*?)<!--\s*/AUTO:\1\s*-->", re.S)
RE_WIKI = re.compile(r"\[\[([^\]\|#]+?)(?:\|[^\]]*)?\]\]")
RE_REL = re.compile(r"\[[^\]]*\]\(([^)\s]+?\.md)\)")
RE_FENCE = re.compile(r"```.*?```", re.S)
RE_CODE = re.compile(r"`[^`\n]*`")
MOLDE = re.compile(r"^(\{|<|nome|outra|nota-[ab]|caminho|alvo|texto|slug|wikilink|exemplo|"
                   r"example|placeholder|Nome$|Name$|X$|TODO)", re.I)
# `YYYY-MM-DD-slug.md` e molde de NOMENCLATURA, nao promessa de arquivo. Documento que
# ensina a convencao cita o molde: acusar isso e acusar a documentacao de existir.
MOLDE_NOME = re.compile(r"(YYYY|AAAA|MM-DD|\{[^}]*\}|<[^>]*>|\bslug\b|\bnome-|N\.md$)", re.I)
LIMITE_STUB = 40          # palavras
DIAS_CAPTURA = 21         # item cru parado no inbox
DIAS_ESTADO = 21          # estado compilado atras do ultimo evento


# ------------------------------------------------------------------ utilitario

def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def frontmatter(txt: str) -> dict:
    if not txt.startswith("---"):
        return {}
    fim = txt.find("\n---", 3)
    if fim < 0:
        return {}
    fm = {}
    for linha in txt[3:fim].splitlines():
        if ":" in linha and not linha.startswith((" ", "-", "#", "\t")):
            k, _, v = linha.partition(":")
            fm[k.strip().lower()] = v.strip()
    return fm


def corpo(txt: str) -> str:
    if txt.startswith("---"):
        fim = txt.find("\n---", 3)
        if fim >= 0:
            return txt[fim + 4:]
    return txt


def sem_codigo(txt: str) -> str:
    """Trecho em crase ou bloco de codigo e documentacao, nao link."""
    return RE_CODE.sub("", RE_FENCE.sub("", txt))


def prosa_util(s: str) -> bool:
    """Uma linha so serve de descricao se ela ABRE uma frase de verdade."""
    if len(s) < 20:
        return False
    if s[0].islower() or s[0] in "{}[]()<>|=/\\\"'#":
        return False
    if s.count(")") > s.count("(") or s.count("}") > s.count("{"):
        return False
    if re.match(r"^(data|link|fonte|status|autor|source|date|participantes)\s*[:=]", s, re.I):
        return False
    return True


def limpa(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    return re.sub(r"[*_`]", "", s).strip()


def descricao(txt: str, limite: int = 100) -> str:
    fm = frontmatter(txt)
    for c in CAMPOS_RESUMO:
        if fm.get(c):
            return fm[c][:limite]
    for exigir_h1 in (True, False):
        visto = not exigir_h1
        for linha in corpo(txt).splitlines():
            b = linha.strip()
            if b.startswith("# "):
                visto = True
                continue
            if not visto or not b or b.startswith(("#", ">", "|", "-", "<!--", "```", "---", "!")):
                continue
            s = limpa(b)
            if prosa_util(s):
                return re.split(r"(?<=[.!?])\s", s)[0][:limite]
    return ""


def data_no_nome(stem: str) -> str | None:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", stem)
    return m.group(1) if m else None


# ------------------------------------------------------------------- inventario

class OS:
    def __init__(self, raiz: Path):
        self.raiz = raiz
        self.notas: list[Path] = []
        for dp, dn, fn in os.walk(raiz):
            dn[:] = [d for d in dn if d not in IGNORE and not d.startswith(".")]
            for f in fn:
                if f.endswith(".md"):
                    self.notas.append(Path(dp) / f)
        self.notas.sort()
        self.txt = {p: p.read_text(encoding="utf-8", errors="replace") for p in self.notas}
        self.fm = {p: frontmatter(t) for p, t in self.txt.items()}
        self.por_base: dict[str, list[Path]] = defaultdict(list)
        for p in self.notas:
            self.por_base[p.stem].append(p)

    def rel(self, p: Path) -> str:
        return str(p.relative_to(self.raiz))

    # ---- reconhecimento: a estrutura, e a regua que ela implica -------------
    def perfil(self) -> dict:
        n = len(self.notas)
        roteadores = [p for p in self.notas if p.name in ROTEADOR]
        convencoes = [p for p in self.notas if p.name in CONVENCAO]
        # indice: nota com o nome da pasta que a contem, ou que lista muitos irmaos
        indices = []
        for p in self.notas:
            if p.stem.lower() == p.parent.name.lower() and p.parent != self.raiz:
                indices.append(p)
        # entidade: pasta com nota-hub homonima E subpastas ou varias notas
        entidades = [p.parent for p in indices
                     if len(list(p.parent.glob("*.md"))) > 1 or any(x.is_dir() for x in p.parent.iterdir())]
        # A raiz nao e pasta de entidade: uma area com nota-indice (comercial/comercial.md)
        # parece um hub, mas e area. Sem esta trava toda area vira "entidade sem estado".
        pai_entidade = Counter(e.parent for e in entidades if e.parent != self.raiz)
        pasta_entidades = [d for d, c in pai_entidade.items() if c >= 2]
        auto = [p for p in self.notas if RE_AUTO.search(self.txt[p])]
        com_fm = [p for p in self.notas if self.fm[p]]
        com_resumo = [p for p in com_fm if any(c in self.fm[p] for c in CAMPOS_RESUMO)]
        com_rev = [p for p in com_fm if any(c in self.fm[p] for c in CAMPOS_DATA_REV)]
        wikilinks = sum(len(RE_WIKI.findall(sem_codigo(t))) for t in self.txt.values())
        relativos = sum(len(RE_REL.findall(sem_codigo(t))) for t in self.txt.values())
        datados = [p for p in self.notas if data_no_nome(p.stem)]
        inbox = [d for d in self.raiz.iterdir()
                 if d.is_dir() and d.name.lower() in NOMES_INBOX]
        estado = [p for p in self.notas
                  if re.search(r"^##+\s*(Estado|State|Status atual)\b", self.txt[p], re.M | re.I)
                  and re.search(r"^##+\s*(Timeline|Histórico|Historico|Log)\b", self.txt[p], re.M | re.I)]
        script = [x for x in (self.raiz / "bin", self.raiz / "scripts")
                  if x.is_dir() and any(x.glob("*.py"))]
        rituais = []
        for d in (self.raiz / ".claude" / "commands", self.raiz / "commands"):
            if d.is_dir():
                rituais += sorted(f.stem for f in d.glob("*.md"))
        tipos = Counter(self.fm[p].get("tipo") or self.fm[p].get("type")
                        for p in com_fm if self.fm[p].get("tipo") or self.fm[p].get("type"))
        return {
            "raiz": str(self.raiz), "notas": n,
            "roteadores": [self.rel(p) for p in roteadores],
            "doc_de_convencao": [self.rel(p) for p in convencoes],
            "indices": [self.rel(p) for p in indices],
            "pastas_de_entidade": [self.rel(d) for d in pasta_entidades],
            "entidades": len(entidades),
            "usa_bloco_auto": len(auto),
            "usa_frontmatter": round(len(com_fm) / n, 2) if n else 0,
            "usa_resumo": round(len(com_resumo) / n, 2) if n else 0,
            "usa_data_de_revisao": round(len(com_rev) / n, 2) if n else 0,
            "wikilinks": wikilinks, "links_relativos": relativos,
            "notas_datadas": len(datados),
            "inbox": [self.rel(d) for d in inbox],
            "estado_compilado": [self.rel(p) for p in estado],
            "camada_de_script": [self.rel(d) for d in script],
            "rituais": rituais,
            "enum_de_tipo": dict(tipos.most_common()),
        }

    # ---- os achados -------------------------------------------------------
    def achados(self, perfil: dict) -> dict:
        prob: dict[str, list] = defaultdict(list)
        entrada = Counter()
        hoje = date.today()

        # A regua adaptativa: so cobra convencao que o OS ja segue na maioria.
        tamanhos = sorted(len(corpo(t_).split()) for t_ in self.txt.values())
        mediana = tamanhos[len(tamanhos) // 2] if tamanhos else 0
        # Densidade de link: um OS que nao linka nao tem nota orfa, tem outra forma.
        densidade = (perfil["wikilinks"] + perfil["links_relativos"]) / max(len(self.notas), 1)
        usa_links = densidade >= 0.3
        exige_fm = perfil["usa_frontmatter"] >= 0.5
        exige_resumo = perfil["usa_resumo"] >= 0.4
        usa_auto = perfil["usa_bloco_auto"] > 0
        usa_wiki = perfil["wikilinks"] >= 5
        indices = [self.raiz / x for x in perfil["indices"]]

        for p in self.notas:
            r, txt = self.rel(p), self.txt[p]
            limpo = sem_codigo(txt)
            # documento que ENSINA a sintaxe: link ali e ilustracao, nao defeito
            didatico = p.name in CONVENCAO or p.name in ROTEADOR \
                or any(x.startswith(("_template", "template")) for x in p.parts)

            for w in RE_WIKI.findall(limpo):
                w = w.strip().removesuffix(".md")
                if not w or MOLDE.match(w):
                    continue
                alvos = self.por_base.get(Path(w).stem, [])
                if not alvos:
                    if not didatico:
                        prob["link_quebrado"].append({"nota": r, "alvo": f"[[{w}]]", "tipo": "wikilink"})
                elif len(alvos) > 1:
                    if not didatico:
                        prob["wikilink_ambiguo"].append(
                            {"nota": r, "alvo": f"[[{w}]]", "resolve_para": len(alvos)})
                else:
                    entrada[alvos[0]] += 1

            for m in RE_REL.findall(limpo):
                if "{" in m or m.startswith(("http", "mailto:")) or MOLDE.match(Path(m).name):
                    continue
                alvo = (p.parent / unquote(m.split("#")[0])).resolve()
                if alvo.exists():
                    entrada[alvo] += 1
                elif not didatico:
                    prob["link_quebrado"].append({"nota": r, "alvo": m, "tipo": "relativo"})

            fm = self.fm[p]
            if exige_fm and not fm and p.name not in ROTEADOR and p.name not in CONVENCAO:
                prob["sem_frontmatter"].append(r)

            palavras = len(corpo(txt).split())
            # Stub e relativo ao PROPRIO OS: 21 palavras e stub num vault de ensaios e
            # tamanho normal num diario. Regua absoluta transforma o estilo da pessoa em defeito.
            if palavras < min(LIMITE_STUB, mediana * 0.4) and p.name not in ROTEADOR \
                    and fm.get("tipo") != "indice" and p not in indices:
                prob["stub"].append({"nota": r, "palavras": palavras, "mediana_do_os": mediana})

            # roteador prometendo o que nao existe
            # So um roteador DO OS promete comando. SKILL.md dentro de skills/ costuma citar
            # caminho de URL (`/clientes`, `/about`), que nao e comando nenhum.
            eh_roteador_do_os = p.name in ROTEADOR and "skills" not in p.parts
            if eh_roteador_do_os and perfil["rituais"]:
                for s in set(re.findall(r"`/([a-z][a-z0-9-]{3,})`", txt)):
                    if MOLDE_NOME.search(s) or s.startswith(("nome", "comando", "skill-")):
                        continue
                    if s not in perfil["rituais"] and not (self.raiz / ".claude" / "skills" / s).exists() \
                            and not (self.raiz / "skills" / s).exists():
                        prob["roteador_fantasma"].append({"nota": r, "cita": f"/{s}"})
            if eh_roteador_do_os:
                for m in set(re.findall(r"`([a-z0-9_./-]+\.md)`", txt, re.I)):
                    if "{" in m or MOLDE.match(Path(m).name) or MOLDE_NOME.search(m) \
                            or re.search(r"\(ex[.:][^)]*`" + re.escape(m) + r"`", txt):
                        continue
                    if Path(m).stem not in self.por_base:
                        prob["roteador_fantasma"].append({"nota": r, "cita": m})

        # orfa: ZERO link de ENTRADA. Nao e "nota sem link", e "nota que ninguem cita".
        # So faz sentido num OS que linka: onde a densidade e baixa, isso vira recomendacao.
        for p in (self.notas if usa_links else []):
            if entrada[p] or p.name in ROTEADOR or p.name in CONVENCAO or p in indices \
                    or p.parent == self.raiz or any(x.startswith(("_template", "template"))
                                                    for x in p.parts):
                continue
            if perfil["inbox"] and any(str(p).startswith(str(self.raiz / i)) for i in perfil["inbox"]):
                continue
            prob["orfa"].append(self.rel(p))

        # tipo usado uma vez so, enquanto outros sao usados muito: deriva, nao categoria
        tipos = perfil["enum_de_tipo"]
        if tipos and max(tipos.values()) >= 5:
            for t, c in tipos.items():
                if c == 1:
                    prob["tipo_orfao"].append({"tipo": t, "usos": c})

        # indice: dois modos, conforme o OS gere ou cure a lista
        for idx in indices:
            pasta = idx.parent
            listados = set()
            for m in RE_REL.findall(self.txt[idx]):
                listados.add((pasta / unquote(m.split("#")[0])).resolve())
            for w in RE_WIKI.findall(self.txt[idx]):
                for a in self.por_base.get(Path(w.strip()).stem, []):
                    listados.add(a.resolve())
            outros_indices = {i.parent for i in indices if i != idx and i.parent != pasta}
            faltando = []
            for f in pasta.rglob("*.md"):
                if f == idx or f.name in ROTEADOR or set(f.parts) & IGNORE:
                    continue
                if any(x.startswith(("_template", "template")) for x in f.parts):
                    continue
                # ja coberto por um indice mais proximo do arquivo
                if any(o in f.parents for o in outros_indices):
                    continue
                if f.resolve() not in listados:
                    faltando.append(self.rel(f))
            if faltando:
                prob["indice_incompleto"].append(
                    {"indice": self.rel(idx), "fora": len(faltando), "ex": faltando[:3]})

            # a frase ao lado de cada item e o que permite decidir sem abrir arquivo
            if exige_resumo or usa_auto:
                for linha in self.txt[idx].splitlines():
                    m = re.match(r"-\s+\[(?:\[)?([^\]]+?)(?:\])?\]"
                                 r"(?:\(([^)]*)\))?\s*(?::\s*(.*))?$", linha.strip())
                    if not m:
                        continue
                    rot, dest, frase = m.group(1), m.group(2), (m.group(3) or "").strip()
                    if frase and prosa_util(frase):
                        continue
                    alvo = (pasta / unquote(dest)).resolve() if dest else None
                    if not alvo:
                        c = self.por_base.get(Path(rot).stem, [])
                        alvo = c[0].resolve() if len(c) == 1 else None
                    if alvo and alvo.exists() and alvo.is_file():
                        prob["resumo_ausente"].append(
                            {"nota": self.rel(Path(alvo)), "indice": self.rel(idx),
                             "frase": frase or "(vazia)"})

        # bloco AUTO so vale se o OS usa: sem gerador, lista curada e legitima
        if usa_auto:
            for p in self.notas:
                for chave, dentro in RE_AUTO.findall(self.txt[p]):
                    if not dentro.strip():
                        prob["bloco_auto_vazio"].append({"nota": self.rel(p), "bloco": chave})

        # nome so de data colide entre pastas e nao pode ser wikilinkado
        if usa_wiki:
            datados = defaultdict(list)
            for p in self.notas:
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem):
                    datados[p.stem].append(self.rel(p))
            for stem, ps in datados.items():
                if len(ps) > 1:
                    prob["nome_datado_colidindo"].append({"nome": stem, "arquivos": ps})

        # duplicata provavel: mesmo basename em pastas diferentes, fora dos genericos
        for base, ps in self.por_base.items():
            if len(ps) > 1 and base not in {x.removesuffix(".md") for x in ROTEADOR | CONVENCAO} \
                    and not any(x.startswith(("_template", "template")) for p in ps for x in p.parts):
                prob["mesmo_nome_em_pastas"].append(
                    {"nome": base, "arquivos": [self.rel(x) for x in ps]})

        # estado compilado: existencia E frescor, nessa ordem
        for d in [self.raiz / x for x in perfil["pastas_de_entidade"]]:
            for ent in sorted(x for x in d.iterdir() if x.is_dir() and x.name not in IGNORE
                              and not x.name.startswith(("_", "."))):
                alvos = [f for f in ent.rglob("*.md")
                         if re.search(r"^##+\s*(Estado|State|Status)\b", self.txt.get(f, ""), re.M | re.I)]
                eventos = [f for f in ent.rglob("*.md") if data_no_nome(f.stem)]
                if not eventos:
                    continue
                if not alvos:
                    prob["entidade_sem_estado"].append(
                        {"entidade": self.rel(ent), "eventos": len(eventos)})
                    continue
                est = alvos[0]
                tem_timeline = bool(re.search(r"^##+\s*(Timeline|Histórico|Historico|Log)\b",
                                              self.txt[est], re.M | re.I))
                if not tem_timeline:
                    prob["estado_sem_timeline"].append({"nota": self.rel(est)})
                d_ev = max(data_no_nome(f.stem) for f in eventos)
                rev = ""
                for c in CAMPOS_DATA_REV:
                    if self.fm[est].get(c):
                        rev = self.fm[est][c][:10]
                        break
                if not rev:
                    prob["estado_sem_data_de_revisao"].append({"nota": self.rel(est)})
                elif rev < d_ev:
                    try:
                        dias = (date.fromisoformat(d_ev) - date.fromisoformat(rev)).days
                    except ValueError:
                        continue
                    if dias > DIAS_ESTADO:
                        prob["estado_defasado"].append(
                            {"nota": self.rel(est), "revisado": rev,
                             "ultimo_evento": d_ev, "dias": dias})

        # captura represada: sintoma de ritual que parou, nao de arquivo
        for i in perfil["inbox"]:
            for f in (self.raiz / i).rglob("*.md"):
                d = data_no_nome(f.stem)
                idade = (hoje - date.fromisoformat(d)).days if d else \
                    (hoje - date.fromtimestamp(f.stat().st_mtime)).days
                if idade > DIAS_CAPTURA:
                    prob["captura_represada"].append({"nota": self.rel(f), "dias": idade})

        return {k: v for k, v in prob.items() if v}

    def recomendacoes(self, perfil: dict) -> list[dict]:
        """Boa pratica que este OS nao tem. NAO e defeito: e escolha, ate a pessoa querer
        mudar. Cada uma vem com o custo de nao ter, e com um limiar de tamanho, porque
        cobrar indice de um OS de 9 notas e ruido."""
        p, n, r = perfil, perfil["notas"], []

        def add(quando, o_que, custo):
            if quando:
                r.append({"recomendacao": o_que, "custo_de_nao_ter": custo})

        add(not p["roteadores"],
            "Criar um roteador na raiz (CLAUDE.md ou SKILL.md)",
            "Sem ele o modelo varre pastas a cada pergunta, em vez de descer por indice")

        grandes = []
        for d in {self.raiz / Path(x).parent for x in
                  [self.rel(f) for f in self.notas] if Path(x).parent != Path(".")}:
            if d.is_dir() and len(list(d.glob("*.md"))) >= 8 \
                    and not (d / f"{d.name}.md").exists():
                grandes.append(self.rel(d))
        add(grandes, f"Criar nota-indice nas pastas com muitas notas: {', '.join(sorted(grandes)[:4])}",
            "Pasta grande sem indice obriga a abrir arquivo por garantia")

        densidade = (p["wikilinks"] + p["links_relativos"]) / max(n, 1)
        add(densidade < 0.3 and n >= 15,
            "Comecar a linkar as notas entre si (wikilink para nome unico, link relativo para o resto)",
            "Sem link as notas nao se correlacionam: cada uma so responde por si")

        add(p["indices"] and p["usa_resumo"] < 0.4,
            "Escrever um campo de resumo no frontmatter das notas que valem ser achadas",
            "Indice sem uma frase por item e lista de nomes: obriga a abrir para saber se serve")

        add(p["pastas_de_entidade"] and not p["estado_compilado"],
            "Dar a cada entidade uma nota de estado com duas camadas (estado de hoje + timeline)",
            "Responder 'como esta isso?' passa a custar a leitura de todos os eventos")

        add(p["estado_compilado"] and p["usa_data_de_revisao"] < 0.2,
            "Adicionar um campo de data de revisao (atualizado:) onde ha estado",
            "Sem ele nao da para saber se a sintese esta velha, e data de arquivo nao serve: "
            "uma edicao em lote faz o OS inteiro parecer atualizado hoje")

        add(not p["inbox"] and n >= 20,
            "Criar uma pasta de captura crua (inbox/), triada so no ritual de revisao",
            "Sem destino unico e sem friccao, a ideia nao entra")

        add(not p["rituais"] and n >= 30,
            "Criar o par de rituais de abrir e fechar o dia",
            "E o unico mecanismo de continuidade entre sessoes: sem ele o OS so responde quando perguntado")

        add(not p["doc_de_convencao"] and n >= 60,
            "Escrever um documento de convencoes (nomes, frontmatter, links)",
            "Acima de ~60 notas a convencao implicita diverge, e ninguem percebe")

        add(not p["camada_de_script"] and n >= 150,
            "Instalar uma camada deterministica que cheque links e indices",
            "Nesse tamanho, verificar a mao gasta modelo e da resposta diferente a cada vez")

        return r


# --------------------------------------------------------------------- saida

SEVERIDADE = {
    # alto: quebram a navegacao, e a maioria e invisivel a olho nu
    "link_quebrado": ("alto", "Link quebrado (relativo nao aparece no grafo: so falha no clique)"),
    "entidade_sem_estado": ("alto", "Entidade com eventos e sem nota de estado: 'como esta isso?' custa ler tudo"),
    "resumo_ausente": ("alto", "Item indexado sem frase util: o indice virou lista de nomes"),
    "indice_incompleto": ("alto", "Arquivo existe e o indice da pasta nao lista"),
    "roteador_fantasma": ("alto", "Roteador citando comando ou arquivo que nao existe"),
    "wikilink_ambiguo": ("alto", "Wikilink que resolve para mais de um arquivo"),
    "estado_defasado": ("medio", "Estado compilado mais velho que o ultimo evento"),
    "estado_sem_timeline": ("medio", "Estado sem camada de historico separada"),
    "estado_sem_data_de_revisao": ("medio", "Estado sem campo de data de revisao"),
    "orfa": ("medio", "Nota com zero link de entrada: ninguem chega nela"),
    "sem_frontmatter": ("medio", "Sem frontmatter onde o OS usa frontmatter"),
    "nome_datado_colidindo": ("medio", "Nome so de data, repetido em pastas diferentes"),
    "captura_represada": ("medio", "Captura parada no inbox: sintoma de ritual que parou"),
    "mesmo_nome_em_pastas": ("baixo", "Mesmo nome de arquivo em pastas diferentes"),
    "bloco_auto_vazio": ("baixo", "Bloco gerado vazio: rodar o gerador"),
    "tipo_orfao": ("baixo", "Valor de tipo usado uma vez so: provavel deriva"),
    "stub": ("baixo", "Nota muito curta: consolidar ou descartar"),
}
ORDEM = {"alto": 0, "medio": 1, "baixo": 2}


def imprime(perfil: dict, prob: dict):
    p = perfil
    print(f"OS em {p['raiz']}")
    print(f"{p['notas']} notas · {p['wikilinks']} wikilinks · {p['links_relativos']} links relativos\n")
    print("## O que este OS usa")
    linhas = [
        ("roteadores", len(p["roteadores"])),
        ("indices de pasta", len(p["indices"])),
        ("entidades (pasta com hub)", p["entidades"]),
        ("blocos gerados (AUTO)", p["usa_bloco_auto"]),
        ("frontmatter", f"{int(p['usa_frontmatter']*100)}% das notas"),
        ("campo de resumo", f"{int(p['usa_resumo']*100)}% das notas"),
        ("campo de data de revisao", f"{int(p['usa_data_de_revisao']*100)}% das notas"),
        ("notas com estado + timeline", len(p["estado_compilado"])),
        ("inbox de captura", ", ".join(p["inbox"]) or "nao"),
        ("camada de script", ", ".join(p["camada_de_script"]) or "nao"),
        ("rituais", ", ".join(p["rituais"]) or "nenhum"),
    ]
    for k, v in linhas:
        print(f"  {k:<28} {v}")
    if p["doc_de_convencao"]:
        print(f"\n  Convencao declarada em {', '.join(p['doc_de_convencao'])}.")
        print("  ELA VENCE este script onde as duas discordarem.")
    else:
        print("\n  Nenhum documento de convencao. A regua abaixo saiu do padrao dominante do proprio OS.")

    if not prob:
        print("\nSem achados: o OS esta consistente consigo mesmo.")
        return
    total = sum(len(v) for v in prob.values())
    print(f"\n## {total} achado(s)\n")
    for k in sorted(prob, key=lambda x: (ORDEM[SEVERIDADE.get(x, ('baixo',''))[0]], -len(prob[x]))):
        sev, desc = SEVERIDADE.get(k, ("baixo", k))
        print(f"[{sev.upper()}] {desc} ({len(prob[k])})")
        for it in prob[k][:8]:
            print("   - " + (it if isinstance(it, str) else
                             "  ".join(f"{a}={b}" for a, b in it.items())))
        if len(prob[k]) > 8:
            print(f"   ... e mais {len(prob[k]) - 8}")
        print()


def imprime_recomendacoes(recs: list[dict]):
    if not recs:
        return
    print(f"\n## {len(recs)} recomendacao(oes): boa pratica que este OS ainda nao tem")
    print("Nao sao defeitos. Sao escolhas, ate a pessoa querer mudar.\n")
    for i, x in enumerate(recs, 1):
        print(f"{i}. {x['recomendacao']}")
        print(f"   custo de nao ter: {x['custo_de_nao_ter']}\n")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    raiz = Path(args[0] if args else ".").resolve()
    if not raiz.is_dir():
        print(f"nao e um diretorio: {raiz}", file=sys.stderr)
        return 2
    os_ = OS(raiz)
    if not os_.notas:
        print(f"nenhum .md em {raiz}", file=sys.stderr)
        return 2
    perfil = os_.perfil()
    prob = {} if "--perfil" in flags else os_.achados(perfil)
    recs = [] if "--perfil" in flags else os_.recomendacoes(perfil)
    if "--json" in flags:
        print(json.dumps({"perfil": perfil, "achados": prob, "recomendacoes": recs,
                          "total": sum(len(v) for v in prob.values())},
                         ensure_ascii=False, indent=2))
    else:
        imprime(perfil, prob)
        imprime_recomendacoes(recs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
