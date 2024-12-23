from dotenv import load_dotenv, find_dotenv
from os import environ
from classes.scrapper import *
from classes.gpt import *

load_dotenv(find_dotenv(), override = True)
if __name__ == "__main__":
    caminho_pdf_original = "./curriculo.pdf"
    load_dotenv(find_dotenv(), override = True)
    # Definir a chave da API da OpenAI
    api_key = environ.get("OPEN_AI_KEY")
    # Lista de descrições de vagas
    descricoes_vagas = [
        """
        Vaga para Desenvolvedor Back-End com experiência em Python, Django e bancos de dados relacionais.
        O candidato deve ter experiência em trabalho remoto e habilidades de liderança.
        """,
        """
        Vaga para Desenvolvedor Full Stack com foco em front-end utilizando React e Vue.js.
        Conhecimentos de CSS e experiência com design responsivo são diferenciais.
        """,
        """
        Vaga para Engenheiro de Dados com habilidades em Spark, Hadoop, e experiência com grandes volumes de dados.
        Experiência em soluções de Big Data e pipeline de dados é essencial.
        """
    ]

    destino_pdfs = "./curriculosgpt"

    processador = ProcessadorCurriculo(caminho_pdf_original, descricoes_vagas, destino_pdfs, api_key)
    processador.processar()