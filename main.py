from dotenv import load_dotenv, find_dotenv
from os import environ
from os.path import abspath
from classes.scrapper import *
from classes.gpt import *
from typing import Any
import pandas as pd
import pdb
import json


def carregar_vagas_existentes(path: str) -> dict:
    """Carrega as vagas já processadas do arquivo JSON."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as json_file:
                vagas = json.load(json_file)
                # Garante que o retorno é um dicionário
                return json.load(vagas) if isinstance(vagas, str) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def atualizar_vagas(vagas_existentes: dict, novas_vagas) -> dict:
    """Atualiza o conjunto de vagas, mantendo o histórico e adicionando novas."""
    novas_vagas_dict = json.loads(novas_vagas.to_json())

    # Combina as vagas existentes com as novas
    vagas_combinadas = {**vagas_existentes, **novas_vagas_dict}
    return vagas_combinadas


if __name__ == "__main__":
    # Configurar credenciais
    load_dotenv(find_dotenv(), override=True)
    credentials = LinkedInCredentials(
        email=environ.get("LINKEDIN_USER"),
        password=environ.get("LINKEDIN_PASS")
    )
    # Definir a chave da API da OpenAI
    api_key = environ.get("OPEN_AI_KEY")

    # Paths
    destino_pdfs = "./curriculosgpt"
    caminho_pdf_original = "./curriculo.pdf"

    # Inicializa o bot do LinkedIn
    bot = LinkedInBot()

    try:
        # Login no LinkedIn
        bot.login(credentials)

        # Busca vagas de desenvolvedor Python no Brasil
        links_de_vagas = bot.buscar_vagas("Desenvolvedor Python", "Brasil")

        # Transformar a estrutura
        df = pd.Series(links_de_vagas)

        # Remover duplicatas
        df_filtrado = df.drop_duplicates()

        # Carrega vagas já processadas
        vagas_existentes = carregar_vagas_existentes("vagas.json")

        # Filtra apenas links que não foram processados anteriormente
        if vagas_existentes:
            links_nao_processados = df_filtrado[~df_filtrado.isin(
                vagas_existentes.keys())]
        else:
            links_nao_processados = df_filtrado

        if not links_nao_processados.empty:
            # Processa apenas novas vagas
            detalhes_vagas: pd.DataFrame = links_nao_processados.apply(
                lambda x: bot.obter_detalhes_vaga(x))
            detalhes_vagas = detalhes_vagas[detalhes_vagas.apply(
                lambda x: x.metodo_apply == 'Interno')]
            detalhes_vagas.reset_index(drop=True, inplace=True)
            # Combina vagas existentes com novas vagas
            vagas_atualizadas = atualizar_vagas(
                vagas_existentes, detalhes_vagas)

            # Salvando como JSON
            with open("vagas.json", "w", encoding="utf-8") as json_file:
                json.dump(vagas_atualizadas, json_file,
                          indent=4, ensure_ascii=False)

            # Processa apenas as novas vagas para gerar currículos
            descricoes_vagas = detalhes_vagas.apply(lambda x: x.descricao)
            processador = ProcessadorCurriculo(
                caminho_pdf_original, descricoes_vagas, destino_pdfs, api_key)

            path_curriculos = processador.processar()
            bot.aplicar_vagas(detalhes_vagas.apply(
                lambda x: x.link), [abspath(path) for path in path_curriculos])

        else:
            print("Não foram encontradas novas vagas para processar.")

    finally:
        # Fechar o navegador
        bot.fechar()
