from medievaia.srd import chapter_type, heading_level, is_noise, join_lines


def test_palavra_hifenizada_na_quebra_de_linha_e_reconstruida():
    assert join_lines(["melee at-", "tacks use Strength"]) == "melee attacks use Strength"


def test_hifen_seguido_de_maiuscula_e_preservado():
    assert join_lines(["a half-", "Orc"]) == "a half- Orc"


def test_tipo_do_conteudo_vem_do_capitulo():
    assert chapter_type("Monsters") == "monster"
    assert chapter_type("Monsters A-Z") == "monster"
    assert chapter_type("Animals") == "monster"
    assert chapter_type("Spells") == "spell"
    assert chapter_type("Classes") == "class"
    assert chapter_type("Capitulo Desconhecido") == "rule"


def test_hierarquia_de_titulos_segue_o_tamanho_da_fonte():
    assert heading_level(26.0) < heading_level(18.0) < heading_level(14.0)
    assert heading_level(10.5) == 3


def test_numero_de_pagina_e_cabecalho_sao_ruido():
    assert is_noise("258")
    assert is_noise("System Reference Document 5.2.1")
    assert not is_noise("Sneak Attack")


def test_titulo_em_versalete_e_recuperado_integralmente(srd_documents):
    titulos = {documento["title"] for documento in srd_documents}

    assert "Exceptions Supersede General Rules" in titulos


def test_nenhum_titulo_fica_indeterminado(srd_documents):
    indeterminados = [
        documento
        for documento in srd_documents
        if not documento["title"] or documento["title"].lower() == "unknown"
    ]

    assert indeterminados == []


def test_todo_documento_tem_capitulo_e_secao(srd_documents):
    assert all(documento["chapter"] for documento in srd_documents)
    assert all(documento["section"] for documento in srd_documents)


def test_secao_nao_vaza_entre_capitulos(srd_documents):
    secoes_por_capitulo = {}
    for documento in srd_documents:
        secoes_por_capitulo.setdefault(documento["chapter"], set()).add(documento["section"])

    assert len(secoes_por_capitulo["Classes"]) == 12
    assert "Rogue" in secoes_por_capitulo["Classes"]
    assert "Rogue" not in secoes_por_capitulo.get("Spells", set())


def test_todos_os_tipos_de_conteudo_sao_extraidos(srd_documents):
    tipos = {documento["type"] for documento in srd_documents}

    assert {"rule", "class", "spell", "monster", "magic_item", "equipment"} <= tipos


def test_documentos_sao_marcados_como_origem_oficial(srd_documents):
    assert all(documento["source_type"] == "srd" for documento in srd_documents)
    assert all(documento["page"] for documento in srd_documents)
