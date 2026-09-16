from medievaia.chunking import MAX_CHARS, OVERLAP_CHARS, chunk_documents, split_content


def test_texto_curto_vira_um_unico_chunk():
    assert split_content("uma regra curta") == ["uma regra curta"]


def test_texto_longo_e_dividido_respeitando_o_limite():
    texto = "\n".join(f"paragrafo {indice} " + "x" * 200 for indice in range(30))
    partes = split_content(texto)

    assert len(partes) > 1
    assert all(len(parte) <= MAX_CHARS + OVERLAP_CHARS for parte in partes)


def test_divisao_preserva_todo_o_conteudo():
    texto = "\n".join(f"regra numero {indice}" for indice in range(400))
    reunido = "".join(split_content(texto))

    assert "regra numero 0" in reunido
    assert "regra numero 399" in reunido


def test_metadados_do_documento_sao_herdados_pelos_chunks():
    documento = {"title": "Ataque Furtivo", "chapter": "Classes", "content": "texto curto"}
    chunks = chunk_documents([documento])

    assert len(chunks) == 1
    assert chunks[0]["title"] == "Ataque Furtivo"
    assert chunks[0]["chapter"] == "Classes"
    assert chunks[0]["part"] == 1
    assert chunks[0]["parts"] == 1


def test_documento_longo_gera_chunks_numerados():
    documento = {"title": "Longo", "content": "\n".join("y" * 300 for _ in range(20))}
    chunks = chunk_documents([documento])

    assert len(chunks) > 1
    assert [chunk["part"] for chunk in chunks] == list(range(1, len(chunks) + 1))
    assert all(chunk["parts"] == len(chunks) for chunk in chunks)
