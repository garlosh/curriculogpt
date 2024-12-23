from openai import OpenAI
import PyPDF2 as pypdf
import os
import hashlib
from fpdf import FPDF
from dataclasses import dataclass
from dotenv import load_dotenv, find_dotenv
from os import environ

@dataclass
class Curriculo:
    caminho_pdf: str
    conteudo: str = ""

    def extrair_conteudo(self):
        """Extrai o conteúdo do arquivo PDF original."""
        try:
            with open(self.caminho_pdf, 'rb') as pdf_file:
                pdf_reader = pypdf.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
                conteudo_extraido = ""
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    conteudo_extraido += page.extract_text() or ""
                self.conteudo = conteudo_extraido
                print("Conteúdo do PDF extraído com sucesso.")
        except Exception as e:
            print(f"Erro ao ler o arquivo PDF: {e}")
            self.conteudo = ""

    def salvar_curriculo_pdf(self, nome_arquivo: str, path: str):
        """Salva o currículo (o atributo 'conteudo' em HTML) em um arquivo PDF na pasta especificada."""
        if not os.path.exists(path):
            os.makedirs(path)

        caminho_completo = os.path.join(path, f"{nome_arquivo}.pdf")

        # Se já existir, não recria
        if os.path.exists(caminho_completo):
            print(f"Currículo já existe e será reaproveitado: {caminho_completo}")
            return
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # No HTMLMixin, usamos o método write_html() para escrever o conteúdo
            pdf.write_html(self.conteudo)

            pdf.output(caminho_completo)
            print(f"Currículo salvo com sucesso em: {caminho_completo}")
        except:
            print(f"Falha ao salvar o curriculo: {nome_arquivo}")


class GeradorCurriculo:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key = self.api_key)

    def gerar_curriculo_personalizado(self, curriculo_original: Curriculo, descricao_vaga: str) -> str:
        """Gera um currículo personalizado com base neste currículo  e na descrição da vaga."""
        prompt = f"""
        A partir do currículo extendido original abaixo:

        {curriculo_original.conteudo}

        E da descrição da vaga:

        {descricao_vaga}

        A partir do currículo original extendido, gere um currículo personalizado que não precise de alterações minhas,
        selecionando os trechos mais adequados, se adequando às palavras chave, enfatizando as habilidades e experiências que mais se alinham com a vaga. 
        Mantenha um tom profissional e objetivo.
        Além disto, retorne apenas o currículo em HTML, pois este será salvo em PDF.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user", "content": prompt}],
            temperature=0.7,
        )
        #pdb.set_trace()
        return response.choices[0].message.content.strip()


class ProcessadorCurriculo:
    def __init__(self, caminho_pdf_original: str, descricoes_vagas: list, destino_pdfs: str, api_key: str):
        self.curriculo = Curriculo(caminho_pdf=caminho_pdf_original)
        self.descricoes_vagas = descricoes_vagas
        self.destino_pdfs = destino_pdfs
        self.api_key = api_key

    def gerar_identificador_unico(self, descricao_vaga: str) -> str:
        """Gera um identificador único baseado na descrição da vaga para nomear o PDF."""
        hash_vaga = hashlib.md5(descricao_vaga.encode()).hexdigest()
        return f"curriculo_{hash_vaga}"

    def processar(self):
        """Processa a geração dos currículos personalizados e os salva como PDFs."""
        # Extrai o conteúdo do currículo original
        self.curriculo.extrair_conteudo()

        # Gera currículos personalizados para cada descrição de vaga
        gerador = GeradorCurriculo(api_key=self.api_key)

        for descricao_vaga in self.descricoes_vagas:
            nome_arquivo = self.gerar_identificador_unico(descricao_vaga)
            caminho_arquivo = os.path.join(self.destino_pdfs, f"{nome_arquivo}.pdf")

            # Verifica se já existe PDF para essa descrição de vaga
            if os.path.exists(caminho_arquivo):
                print(f"Currículo já existente para esta vaga: {nome_arquivo}.pdf. Reutilizando...")
                continue

            # Gera o texto personalizado
            curriculo_personalizado = gerador.gerar_curriculo_personalizado(self.curriculo, descricao_vaga)

            # Cria um novo objeto Curriculo apenas com o conteúdo personalizado
            curriculo_temp = Curriculo(caminho_pdf="", conteudo=curriculo_personalizado)
            curriculo_temp.salvar_curriculo_pdf(nome_arquivo, self.destino_pdfs)


# Função principal para executar o fluxo de geração de múltiplos currículos
def main():
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


if __name__ == "__main__":
    main()
