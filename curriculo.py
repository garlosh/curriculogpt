import openai
import PyPDF2 as pypdf
import os
import hashlib
from fpdf import FPDF
from dataclasses import dataclass
from gpt import *
# Definir a chave da API da OpenAI
openai.api_key = 'SUA_CHAVE_API_OPENAI'

@dataclass
class Curriculo:
    caminho_pdf: str
    conteudo: str = ""

    def extrair_conteudo(self):
        """Extrai o conteúdo do arquivo PDF original."""
        try:
            with open(self.caminho_pdf, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
                conteudo = ""
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    conteudo += page.extract_text()
                self.conteudo = conteudo
                print(f"Conteúdo do PDF extraído com sucesso.")
        except Exception as e:
            print(f"Erro ao ler o arquivo PDF: {e}")
            self.conteudo = ""

    def salvar_curriculo_pdf(self, nome_arquivo: str, path: str):
        """Salva o currículo gerado em um arquivo PDF na pasta especificada."""
        if not os.path.exists(path):
            os.makedirs(path)

        caminho_completo = os.path.join(path, f"{nome_arquivo}.pdf")

        if os.path.exists(caminho_completo):
            print(f"Currículo já existe e será reaproveitado: {caminho_completo}")
            return

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Adiciona conteúdo ao PDF, linha por linha
        for linha in self.conteudo.split('\n'):
            pdf.multi_cell(0, 10, linha)
        
        pdf.output(caminho_completo)
        print(f"Currículo salvo com sucesso em: {caminho_completo}")
   

class GeradorCurriculo:
    def __init__(self, api_key: str):
        self.api_key = api_key


    def gerar_curriculo_personalizado(self, curriculo_original: Curriculo, descricao_vaga: str) -> str:
        """Gera um currículo personalizado com base no currículo original e na descrição da vaga."""
        prompt = f"""
        A partir do currículo original abaixo:

        {curriculo_original.conteudo}

        E da descrição da vaga:

        {descricao_vaga}

        Gere um currículo personalizado, enfatizando as habilidades e experiências que mais se alinham com a vaga.
        """
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1500,
            temperature=0.7,
        )
        
        return response['choices'][0]['text']



class ProcessadorCurriculo:
    def __init__(self, caminho_pdf_original: str, descricoes_vagas: list, destino_pdfs: str):
        self.curriculo = Curriculo(caminho_pdf=caminho_pdf_original)
        self.descricoes_vagas = descricoes_vagas
        self.destino_pdfs = destino_pdfs

    def gerar_identificador_unico(self, descricao_vaga: str) -> str:
        """Gera um identificador único baseado na descrição da vaga para evitar duplicação."""
        # Gerar um hash da descrição da vaga para criar um nome de arquivo único
        hash_vaga = hashlib.md5(descricao_vaga.encode()).hexdigest()
        return f"curriculo_{hash_vaga}"

    def processar(self):
        """Processa a geração dos currículos personalizados e os salva como PDFs."""
        # Extrai o conteúdo do currículo original
        self.curriculo.extrair_conteudo()

        # Gera currículos personalizados para cada descrição de vaga
        gerador = GeradorCurriculo(api_key=openai.api_key)
        escritor_pdf = pypdf.PdfWriter(pasta_destino=self.destino_pdfs) 

        for descricao_vaga in self.descricoes_vagas:
            nome_arquivo = self.gerar_identificador_unico(descricao_vaga)
            
            # Verifica se o currículo já existe para essa descrição de vaga
            if os.path.exists(os.path.join(self.destino_pdfs, f"{nome_arquivo}.pdf")):
                print(f"Currículo já existente para esta vaga: {nome_arquivo}.pdf. Reutilizando...")
                continue

            # Gera o currículo personalizado
            curriculo_personalizado = gerador.gerar_curriculo_personalizado(self.curriculo, descricao_vaga)

            # Salva o currículo personalizado em PDF
            escritor_pdf.salvar_curriculo_pdf(curriculo_personalizado, nome_arquivo)


# Função principal para executar o fluxo de geração de múltiplos currículos
def main():
    caminho_pdf_original = "./curriculo.pdf"
    import pdb
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

    processador = ProcessadorCurriculo(caminho_pdf_original, descricoes_vagas, destino_pdfs)
    processador.processar()

# Executa o script principal
if __name__ == "__main__":
    main()
