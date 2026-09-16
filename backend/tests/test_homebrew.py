from medievaia.homebrew import parse_homebrew

REGRAS = """# Regras da Casa

## Acerto Critico Brutal

Um acerto critico causa dano maximo em vez de rolar os dados novamente.

## Descanso Curto Acelerado

Um descanso curto leva 10 minutos em vez de 1 hora.
"""


def escrever(pasta, nome, conteudo):
    caminho = pasta / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def test_cada_secao_vira_um_documento(tmp_path):
    escrever(tmp_path, "regras_da_casa.md", REGRAS)

    documentos = parse_homebrew(tmp_path)

    assert [documento["title"] for documento in documentos] == [
        "Acerto Critico Brutal",
        "Descanso Curto Acelerado",
    ]


def test_hierarquia_do_markdown_vira_capitulo_e_secao(tmp_path):
    escrever(tmp_path, "regras_da_casa.md", REGRAS)

    documento = parse_homebrew(tmp_path)[0]

    assert documento["chapter"] == "Regras da Casa"
    assert documento["section"] == "Acerto Critico Brutal"


def test_origem_e_marcada_como_homebrew(tmp_path):
    escrever(tmp_path, "regras_da_casa.md", REGRAS)

    documento = parse_homebrew(tmp_path)[0]

    assert documento["source_type"] == "homebrew"
    assert documento["source_name"] == "regras_da_casa"
    assert documento["type"] == "homebrew"
    assert documento["page"] is None


def test_secao_sem_conteudo_relevante_e_descartada(tmp_path):
    escrever(tmp_path, "vazio.md", "# Titulo\n\n## Secao\n\ncurto\n")

    assert parse_homebrew(tmp_path) == []


def test_arquivos_de_outras_extensoes_sao_ignorados(tmp_path):
    escrever(tmp_path, "notas.pdf", REGRAS)
    escrever(tmp_path, "notas.txt", REGRAS)

    documentos = parse_homebrew(tmp_path)

    assert {documento["source_name"] for documento in documentos} == {"notas"}


def test_pasta_inexistente_nao_quebra(tmp_path):
    assert parse_homebrew(tmp_path / "nao_existe") == []
