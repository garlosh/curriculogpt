from dotenv import load_dotenv, find_dotenv
from os import environ
from classes.scrapper import *
from classes.gpt import *
import pandas as pd
import pdb

if __name__ == "__main__":
    # Configurar credenciais
    load_dotenv(find_dotenv(), override = True)
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
        detalhes_vagas = df_filtrado.apply(lambda x: bot.obter_detalhes_vaga(x))
        detalhes_vagas = detalhes_vagas[detalhes_vagas.apply(lambda x: x.metodo_apply == 'Interno')]

        # Salvando como JSON
        with open("vagas.json", "w", encoding="utf-8") as json_file:
            json.dump(detalhes_vagas.to_json(), json_file, indent=4, ensure_ascii=False)
    finally:
        # Fechar o navegador
        bot.fechar()

    descricoes_vagas = detalhes_vagas.apply(lambda x: x.descricao)
    processador = ProcessadorCurriculo(caminho_pdf_original, descricoes_vagas, destino_pdfs, api_key)
    processador.processar()