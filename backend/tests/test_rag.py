from medievaia.rag import SYSTEM_PROMPT, format_context

OFICIAL = {
    "source_type": "srd",
    "source_name": "SRD 5.2.1",
    "page": 61,
    "chapter": "Classes",
    "section": "Rogue",
    "title": "Level 1: Sneak Attack",
    "type": "class",
    "content": "Uma vez por turno voce causa dano extra.",
}

DA_CASA = {
    "source_type": "homebrew",
    "source_name": "mesa_do_joao",
    "page": None,
    "chapter": "Regras da Casa",
    "section": "Critico",
    "title": "Acerto Critico Brutal",
    "type": "homebrew",
    "content": "Critico causa dano maximo.",
}


def test_origem_oficial_e_da_casa_recebem_marcadores_distintos():
    contexto = format_context([OFICIAL, DA_CASA])

    assert "[SRD]" in contexto
    assert "[HOMEBREW]" in contexto


def test_contexto_expoe_a_procedencia_de_cada_trecho():
    contexto = format_context([OFICIAL])

    assert "SRD 5.2.1" in contexto
    assert "pagina 61" in contexto
    assert "Classes > Rogue" in contexto
    assert "Level 1: Sneak Attack" in contexto


def test_trecho_sem_pagina_e_identificado():
    assert "sem pagina" in format_context([DA_CASA])


def test_trechos_sao_separados_entre_si():
    contexto = format_context([OFICIAL, DA_CASA])

    assert contexto.count("---") == 1


def test_instrucoes_exigem_resposta_fundamentada_e_citada():
    assert "SOMENTE com base nos trechos" in SYSTEM_PROMPT
    assert "Nunca invente regras" in SYSTEM_PROMPT
    assert "divergencia" in SYSTEM_PROMPT
