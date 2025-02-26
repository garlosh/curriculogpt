from openai import OpenAI
import PyPDF2 as pypdf
import os
import hashlib
from fpdf import FPDF
from dataclasses import dataclass
# from dotenv import load_dotenv, find_dotenv
# from os import environ
from pandas import Series
import pdb


@dataclass
class Curriculo:
    caminho_pdf: str
    conteudo: str = ""

    def extrair_conteudo(self) -> None:
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

    def salvar_curriculo_pdf(self, nome_arquivo: str, path: str) -> None:
        """Salva o currículo (o atributo 'conteudo' em HTML) em um arquivo PDF na pasta especificada."""
        if not os.path.exists(path):
            os.makedirs(path)

        caminho_completo = os.path.join(path, f"{nome_arquivo}.pdf")

        # Se já existir, não recria
        if os.path.exists(caminho_completo):
            print(
                f"Currículo já existe e será reaproveitado: {caminho_completo}")
            return
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.write_html(self.conteudo)
            pdf.output(caminho_completo)
            print(f"Currículo salvo com sucesso em: {caminho_completo}")
        except:
            print(f"Falha ao salvar o curriculo: {nome_arquivo}")


class GeradorCurriculo:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def gerar_curriculo_personalizado(self, curriculo_original: Curriculo, descricao_vaga: str) -> str:
        """Gera um currículo personalizado com base neste currículo e na descrição da vaga."""
        prompt = f"""
        Este é o currículo extendido original abaixo:

        {curriculo_original.conteudo}

        E a descrição da vaga de emprego:

        {descricao_vaga}
        Assim, sua tarefa é a seguinte:
        - Gerar um currículo personalizado para a vaga informada a partir do currículo original extendido.
        - O currículo deve ser gerado em HTML, mas não é necessário gerar um cabeçalho, apenas o corpo do curriculo.
        - Você deve selecionar as experiências que mais se alinham com a vaga, enfatizando as habilidades e experiências que mais se destacam.
        - Mantenha um tom profissional e objetivo.
        - Não gaste muito espaço com a apresentação, foque nas experiências e habilidades.
        - Gere o conteúdo de forma que o currículo preencha uma página mais ou menos, com bastante foco nas experiências.
        - Lembre-se que este currículo será convertido em PDF, portanto é de suma importância que o HTML gerado seja válido.
        - Não adicione nenhum comentário seu sobre o currículo, apenas o currículo em si.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
        )
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

    def processar(self) -> Series:
        """Processa a geração dos currículos personalizados e os salva como PDFs."""
        # Extrai o conteúdo do currículo original
        self.curriculo.extrair_conteudo()

        # Gera currículos personalizados para cada descrição de vaga
        gerador = GeradorCurriculo(api_key=self.api_key)
        resultado = Series([''] * len(self.descricoes_vagas))
        cont = 0
        for descricao_vaga in self.descricoes_vagas:
            nome_arquivo = self.gerar_identificador_unico(descricao_vaga)
            caminho_arquivo = os.path.join(
                self.destino_pdfs, f"{nome_arquivo}.pdf")

            # Verifica se já existe PDF para essa descrição de vaga
            if os.path.exists(caminho_arquivo):
                print(
                    f"Currículo já existente para esta vaga: {nome_arquivo}.pdf. Reutilizando...")
                continue

            # Gera o texto personalizado
            curriculo_personalizado = gerador.gerar_curriculo_personalizado(
                self.curriculo, descricao_vaga).replace("`", "").replace("`", "").replace("html", "")

            # Cria um novo objeto Curriculo apenas com o conteúdo personalizado
            curriculo_temp = Curriculo(
                caminho_pdf="", conteudo=curriculo_personalizado)
            curriculo_temp.salvar_curriculo_pdf(
                nome_arquivo, self.destino_pdfs)
            resultado[cont] = caminho_arquivo
        return resultado
