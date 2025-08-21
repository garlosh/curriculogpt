from dotenv import load_dotenv, find_dotenv
from os import environ
from os.path import abspath
from classes.scrapper import *
from classes.gpt import *
from typing import Any
import pandas as pd
import json


def carregar_vagas_existentes(path: str) -> pd.DataFrame:
    """Carrega as vagas já processadas do arquivo JSON como DataFrame."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as json_file:
                vagas_dict = json.load(json_file)
                # Verifica se o arquivo está vazio ou não é válido
                if not vagas_dict:
                    return pd.DataFrame()
                # Converte o dicionário para DataFrame
                return pd.DataFrame.from_dict(vagas_dict, orient='index').reset_index().drop(columns='index')
        except (json.JSONDecodeError, ValueError):
            return pd.DataFrame()
    return pd.DataFrame()


def atualizar_vagas(vagas_existentes: pd.DataFrame, novas_vagas: pd.DataFrame) -> pd.DataFrame:
    # """Atualiza o conjunto de vagas, mantendo o histórico e adicionando novas."""
    if vagas_existentes.empty:
        return novas_vagas
    for df in [vagas_existentes, novas_vagas]:
        if 'link' not in df.columns and 'index' in df.columns:
            df.rename(columns={'index': 'link'}, inplace=True)
        df.reset_index(drop=True, inplace=True)

    vagas_combinadas = pd.concat(
        [vagas_existentes, novas_vagas], ignore_index=True)

    return vagas_combinadas.drop_duplicates(subset='link', keep='last').reset_index(drop=True)


def salvar_mapeamento_curriculos_vagas(path_curriculos: pd.Series, detalhes_vagas: pd.DataFrame, destino: str) -> None:
    """
    Salva um arquivo txt que mapeia os currículos para suas respectivas vagas.
    """
    if len(path_curriculos) != len(detalhes_vagas):
        print("Erro: O número de currículos não corresponde ao número de vagas.")
        return
    # Cria um DataFrame de mapeamento
    mapeamento = pd.DataFrame({
        'caminho_curriculo': path_curriculos,
        'link_vaga': detalhes_vagas['link'],
        'estilo_trabalho': detalhes_vagas['estilo_trabalho'],
        'nivel_senioridade': detalhes_vagas['nivel_senioridade'],
        'data_aplicacao': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    })

    # Garante que o diretório de destino existe
    os.makedirs(os.path.dirname(destino), exist_ok=True)

    # Salva como CSV para melhor estruturação
    mapeamento.to_csv(destino, index=False)

    # Também salva como texto formatado para leitura humana
    with open(destino.replace('.csv', '.txt'), 'w', encoding='utf-8') as f:
        f.write("MAPEAMENTO DE CURRÍCULOS PARA VAGAS\n")
        f.write("Data de geração: " +
                pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")

        for i, row in mapeamento.iterrows():
            f.write(
                f"Currículo: {os.path.basename(row['caminho_curriculo'])}\n")
            f.write(f"Vaga: {row['link_vaga']}\n")
            f.write(f"Estilo de Trabalho: {row['estilo_trabalho']}\n")
            f.write(f"Nível de Senioridade: {row['nivel_senioridade']}\n")
            f.write(f"Data de Aplicação: {row['data_aplicacao']}\n")
            f.write("-" * 80 + "\n\n")


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
    mapeamento_path = os.path.join(
        destino_pdfs, "mapeamento_curriculos_vagas.csv")

    # Inicializa o bot do LinkedIn
    bot = LinkedInBot()

    try:
        bot.login(credentials)

        # Busca vagas de desenvolvedor Python no Brasil
        links_de_vagas = bot.buscar_vagas("Desenvolvedor Python", "Brasil")

        # Transformar para DataFrame
        df_vagas = pd.DataFrame(links_de_vagas, columns=['link'])

        # Remover duplicatas
        df_vagas = df_vagas.drop_duplicates()

        # Carrega vagas já processadas
        vagas_existentes = carregar_vagas_existentes("vagas.json")

        # Filtra apenas links que não foram processados anteriormente
        if not vagas_existentes.empty:
            links_nao_processados = df_vagas[~df_vagas['link'].isin(
                vagas_existentes['link'])]
        else:
            links_nao_processados = df_vagas

        if not links_nao_processados.empty:
            print(f"Processando {len(links_nao_processados)} novas vagas...")

            # Processa apenas novas vagas
            detalhes_novas_vagas = pd.DataFrame(
                columns=['link', 'estilo_trabalho', 'nivel_senioridade', 'metodo_apply', 'descricao'])

            for idx, row in links_nao_processados.iterrows():
                vaga = bot.obter_detalhes_vaga(row['link'])
                if vaga and vaga.metodo_apply == 'Interno':
                    nova_linha = pd.DataFrame({
                        'link': [vaga.link],
                        'estilo_trabalho': [vaga.estilo_trabalho],
                        'nivel_senioridade': [vaga.nivel_senioridade],
                        'metodo_apply': [vaga.metodo_apply],
                        'descricao': [vaga.descricao]
                    })
                    detalhes_novas_vagas = pd.concat(
                        [detalhes_novas_vagas, nova_linha], ignore_index=True)
            # import ipdb
            # ipdb.set_trace()
            # Combina vagas existentes com novas vagas
            vagas_atualizadas = atualizar_vagas(
                vagas_existentes, detalhes_novas_vagas)

            # Salvando como JSON formatado
            with open("vagas.json", "w", encoding="utf-8") as json_file:
                json.dump(vagas_atualizadas.to_dict(orient='index'),
                          json_file, indent=4, ensure_ascii=False)

            if not detalhes_novas_vagas.empty:
                # Processa apenas as novas vagas para gerar currículos
                descricoes_vagas = detalhes_novas_vagas['descricao']
                processador = ProcessadorCurriculo(
                    caminho_pdf_original, descricoes_vagas, destino_pdfs, api_key)

                path_curriculos = processador.processar()

                # Salva o mapeamento entre currículos e vagas
                salvar_mapeamento_curriculos_vagas(
                    path_curriculos, detalhes_novas_vagas, mapeamento_path)

                # Aplica os currículos às vagas
                bot.aplicar_vagas(detalhes_novas_vagas['link'].tolist(),
                                  [abspath(path) for path in path_curriculos])
            else:
                print(
                    "Não foram encontradas novas vagas com método de aplicação interno.")
        else:
            print("Não foram encontradas novas vagas para processar.")

    finally:
        # Fechar o navegador
        bot.fechar()
