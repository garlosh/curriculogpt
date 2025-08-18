from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from dataclasses import dataclass
from typing import Optional
import random
import numpy as np
import multiprocessing
import time
import pdb
# Usando dataclass para armazenar informações de login


@dataclass
class LinkedInCredentials:
    email: str
    password: str


@dataclass
class Vaga:
    link: str
    estilo_trabalho: str
    nivel_senioridade: str
    metodo_apply: str
    descricao: str

# Falta adequar isso


def parallelize(funct, iterable, processes=None) -> np.array:
    num_nucleos = multiprocessing.cpu_count() - 1 if processes is None else processes
    print(f"Número de núcleos disponíveis: {num_nucleos}")
    resultados = np.array([])
    with multiprocessing.Pool(processes=num_nucleos) as pool:

        for i in pool.imap_unordered(funct, iterable):
            resultados = np.append(resultados, i)

    return resultados


class LinkedInBot:
    def __init__(self):
        service = Service(
            executable_path="C:\\Users\\cagol\\OneDrive\\Documentos\\Projetos\\curriculogpt\\driver\\msedgedriver.exe")
        self.driver: webdriver.Edge = webdriver.Edge(service=service)

    def login(self, credentials: LinkedInCredentials) -> None:
        """Realiza login no LinkedIn."""
        self.driver.maximize_window()
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)

        # Preenche o campo de e-mail e senha
        email_field = self.driver.find_element(By.ID, "username")
        email_field.send_keys(credentials.email)

        password_field = self.driver.find_element(By.ID, "password")
        password_field.send_keys(credentials.password)

        # Submete o formulário
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

    def buscar_vagas(self, palavra_chave: str, localizacao: str) -> np.array:
        """Busca vagas no LinkedIn e retorna os links das vagas."""
        self.driver.get(
            f"https://www.linkedin.com/jobs/search/?keywords={palavra_chave}&location={localizacao}")
        time.sleep(5)

        links_vagas = []
        import pdb

        # Coleta os links das vagas
        try:
            pags_root = self.driver.find_elements(
                By.XPATH, "//li[@data-test-pagination-page-btn]")

            if pags_root:
                # Funções para extrair dados dos elementos
                def get_pag_number(element):
                    try:
                        return int(element.get_attribute('data-test-pagination-page-btn'))
                    except (ValueError, TypeError):
                        return 1

                def get_link(element):
                    return element.get_attribute('href')

                # Obtém o número máximo de páginas
                page_numbers = [get_pag_number(elem) for elem in pags_root]
                max_page = max(page_numbers) if page_numbers else 1
                max_start = 25 * max_page
            else:
                max_start = 25  # Se não encontrar paginação, busca apenas a primeira página

        except Exception as e:
            print(f"Erro ao obter informações de paginação: {e}")
            max_start = 25
        # Itera pelas páginas
        for i in range(0, min(max_start, 250), 25):
            try:
                # Navega para a página específica
                self.driver.get(
                    f"https://www.linkedin.com/jobs/search/?keywords={palavra_chave}&f_AL=true&location={localizacao}&start={i}")
                time.sleep(6)

                # Scroll até o fim da página
                try:
                    footer = self.driver.find_element(
                        By.XPATH, "//ul[contains(@class, 'artdeco-pagination__pages')]")
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", footer)
                except:
                    # Se não encontrar o footer, faz scroll até o final da página
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")

                time.sleep(8)

                # Coleta os links das vagas na página atual
                vagas_elements = self.driver.find_elements(
                    By.XPATH, "//a[contains(@class, 'job-card-list__title')]")

                for vaga_elem in vagas_elements:
                    link = vaga_elem.get_attribute('href')
                    if link and link not in links_vagas:
                        links_vagas.append(link)

                print(
                    f"Página {i // 25 + 1}: Encontradas {len(vagas_elements)} vagas")

            except Exception as e:
                print(f"Erro ao processar página {i // 25 + 1}: {e}")
                continue

        print(f"Total de vagas únicas encontradas: {len(links_vagas)}")
        return np.array(links_vagas)

    def obter_detalhes_vaga(self, link_vaga: str) -> Optional['Vaga']:
        """Navega até a vaga e coleta detalhes, incluindo estilo de trabalho, senioridade e método de apply."""
        self.driver.get(link_vaga)
        time.sleep(random.randint(5, 10))

        try:
            # Estilo de trabalho (Remoto, Híbrido, Presencial)
            estilo_trabalho = "Indefinido"
            try:
                estilo_trabalho_elem = self.driver.find_element(
                    By.XPATH, "//span[contains(text(), 'Remoto') or contains(text(), 'Híbrido') or contains(text(), 'Presencial')]")
                estilo_trabalho = estilo_trabalho_elem.text
            except:
                pass

            # Nível de senioridade
            nivel_senioridade = "Indefinido"
            try:
                nivel_senioridade_elem = self.driver.find_element(
                    By.XPATH, "//span[@dir and contains(@class, 'job-details-jobs-unified-top-card__job-insight-view-model-secondary')]")
                nivel_senioridade = nivel_senioridade_elem.text
            except:
                pass

            # Método de candidatura (Easy Apply, Apply Externo, ou Apply)
            metodo_apply = "Indefinido"
            try:
                apply_btn_elem = self.driver.find_element(
                    By.CLASS_NAME, "jobs-apply-button").get_attribute("aria-label")
                if apply_btn_elem.lower().find("candidatura") != -1:
                    metodo_apply = "Interno"
                else:
                    metodo_apply = "Externo"

            except:
                pass

            # Descrição da vaga
            desc = "Indefinido"
            try:
                # Não precisa salvar na memória
                self.driver.find_element(
                    By.XPATH, "//button[contains(@class, 'jobs-description__footer-button')]").click()
                desc_elem = self.driver.find_element(
                    By.XPATH, "//*[@id='job-details']/div")
                desc = desc_elem.text
            except:
                pass
            # Retorna as informações da vaga
            return Vaga(
                link=link_vaga,
                estilo_trabalho=estilo_trabalho,
                nivel_senioridade=nivel_senioridade,
                metodo_apply=metodo_apply,
                descricao=desc
            )

        except Exception as e:
            print(
                f"Erro ao obter detalhes da vaga: {link_vaga}, erro: {str(e)}")
            return None

    def aplicar_vagas(self, links_vagas: list, caminhos_curriculos: list) -> dict:
        """
        Itera sobre uma lista de links de vagas e seus currículos correspondentes.

        Args:
            links_vagas: Lista de links das vagas para aplicar
            caminhos_curriculos: Lista de caminhos para os arquivos de currículo PDF (na mesma ordem dos links)

        Returns:
            Dicionário com resultados das aplicações: {link: status}
        """
        resultados = {}

        # Verifica se as listas têm o mesmo tamanho
        if len(links_vagas) != len(caminhos_curriculos):
            print(
                f"AVISO: Número de links ({len(links_vagas)}) diferente do número de currículos ({len(caminhos_curriculos)})")
            # Usa apenas até onde as listas têm correspondência
            num_aplicacoes = min(len(links_vagas), len(caminhos_curriculos))
            links_vagas = links_vagas[:num_aplicacoes]
            caminhos_curriculos = caminhos_curriculos[:num_aplicacoes]

        # Itera sobre os pares de links e currículos
        for link, caminho_curriculo in zip(links_vagas, caminhos_curriculos):
            try:
                self.driver.get(link)
                time.sleep(5)

                # Verifica se existe botão de "Candidatura Simplificada"
                try:
                    aplicar_btn = self.driver.find_elements(
                        By.CLASS_NAME, "jobs-apply-button")

                    if not aplicar_btn[1].is_displayed() or not aplicar_btn[1].is_enabled():
                        resultados[link] = "Botão de aplicação não disponível"
                        continue

                    aplicar_btn[1].click()
                    time.sleep(3)
                    # pdb.set_trace()  # Removido o debugger break point

                    # Verifica se há um campo para upload de currículo
                    try:
                        # Tenta encontrar o elemento de upload
                        upload_element = self.driver.find_element(
                            By.CSS_SELECTOR, "input[type='file']")

                        # Envia o caminho do arquivo
                        upload_element.send_keys(caminho_curriculo)
                        time.sleep(2)

                        # Tenta encontrar e clicar no botão de envio/próximo
                        next_or_submit_btn = self.driver.find_element(
                            By.XPATH,
                            "//button[.//span[contains(normalize-space(), 'Enviar Candidatura')]]"
                        )
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView(true);", next_or_submit_btn)
                        next_or_submit_btn.click()
                        time.sleep(2)

                        # Registra resultado como sucesso
                        resultados[link] = "Aplicação enviada com sucesso"
                        print(f"Candidatura enviada para: {link}")

                    except Exception as e:
                        resultados[link] = f"Erro no upload do currículo: {str(e)}"
                        print(f"Erro ao fazer upload do currículo: {str(e)}")

                except Exception as e:
                    resultados[link] = f"Erro ao clicar no botão de candidatura: {str(e)}"
                    print(f"Erro ao clicar no botão de candidatura: {str(e)}")

            except Exception as e:
                resultados[link] = f"Erro ao acessar a vaga: {str(e)}"
                print(f"Erro ao acessar a vaga {link}: {str(e)}")

            # Pausa entre aplicações para evitar detecção de automação
            time.sleep(random.randint(3, 7))

        return resultados

    def fechar(self) -> None:
        """Fecha o navegador."""
        self.driver.quit()
