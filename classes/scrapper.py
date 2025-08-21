from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
import pyautogui
from selenium.webdriver.common.by import By
from dataclasses import dataclass
from typing import Optional
from classes.gpt import InterfaceIA, Curriculo
import random
import numpy as np
import time
import ipdb
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


class LinkedInBot:
    def __init__(self, api_key: str):
        opt = webdriver.EdgeOptions()
        opt.add_argument("--log-level=3")
        service = Service(
            executable_path="C:\\Users\\cagol\\OneDrive\\Documentos\\Projetos\\curriculogpt\\driver\\msedgedriver.exe")
        self.driver: webdriver.Edge = webdriver.Edge(
            service=service, options=opt)
        self.interface_ia = InterfaceIA(api_key)

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

    def buscar_vagas(self, palavra_chave: str, localizacao: str, max_vagas=25) -> np.array:
        """Busca vagas no LinkedIn e retorna os links das vagas."""
        links_vagas = []
        self.driver.get(
            f"https://www.linkedin.com/jobs/search/?keywords={palavra_chave}&location={localizacao}")
        time.sleep(5)

        for i in range(0, 10):
            pyautogui.hotkey('ctrl', '-')
            time.sleep(0.2)

        time.sleep(2)

        # Itera pelas páginas
        for i in range(0, max_vagas, 25):
            try:
                # Navega para a página específica
                self.driver.get(
                    f"https://www.linkedin.com/jobs/search/?keywords={palavra_chave}&f_AL=true&location={localizacao}&start={i}")
                time.sleep(3)

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

        try:
            self.driver.get(link_vaga)
            time.sleep(random.randint(5, 10))
            self.driver.execute_script("window.stop();")
            # Estilo de trabalho (Remoto, Híbrido, Presencial)
            estilo_trabalho = "Indefinido"
            try:
                estilo_trabalho_elem = self.driver.find_element(
                    By.XPATH, "//span[contains(text(), 'Remoto') or contains(text(), 'Híbrido') or contains(text(), 'Presencial')]")
                estilo_trabalho = estilo_trabalho_elem.text
            except Exception:
                pass

            # Nível de senioridade
            nivel_senioridade = "Indefinido"
            try:
                nivel_senioridade_elem = self.driver.find_element(
                    By.XPATH, "//span[@dir and contains(@class, 'job-details-jobs-unified-top-card__job-insight-view-model-secondary')]")
                nivel_senioridade = nivel_senioridade_elem.text
            except Exception:
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

            except Exception:
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
            except Exception:
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

    def _send_or_advance_apply(self):
        result = None
        try:
            # Tenta encontrar e clicar no botão de envio/próximo
            next_or_submit_btn = self.driver.find_element(
                By.XPATH,
                "//button[.//span[contains(normalize-space(), 'Enviar Candidatura')]]"
            )
            result = 'Enviar Candidatura'
        except:
            next_or_submit_btn = self.driver.find_element(
                By.XPATH,
                "//button[.//span[contains(normalize-space(), 'Avançar') or contains(normalize-space(), 'Revisar')]]"
            )
            result = 'Avançar'
        next_or_submit_btn.click()
        return result

    def _define_page_type(self):
        result = None
        try:
            upload_element = self.driver.find_element(
                By.XPATH, "//h3[@class='t-16 t-bold']")
            result = upload_element.text
        except:
            return None

        return result

    def aplicar_vagas(self, links_vagas: list, caminhos_curriculos: list, curriculo: Curriculo) -> dict:
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

                aplicar_btn = self.driver.find_elements(
                    By.CLASS_NAME, "jobs-apply-button")

                if not aplicar_btn[1].is_displayed() or not aplicar_btn[1].is_enabled():
                    resultados[link] = "Botão de aplicação não disponível"
                    continue

                aplicar_btn[1].click()
                time.sleep(1.5)
                # pdb.set_trace()  # Removido o debugger break point

                # Verifica se há um campo para upload de currículo

                out = False
                while not out:
                    result = self._send_or_advance_apply()
                    if result == 'Enviar Candidatura':
                        out = True
                    time.sleep(1)
                    page_type = self._define_page_type()

                    if page_type and page_type == 'Currículo':
                        upload_element = self.driver.find_element(
                            By.CSS_SELECTOR, "input[type='file']")
                        upload_element.send_keys(caminho_curriculo)

                    elif page_type and page_type == 'Perguntas adicionais':
                        questions = self.driver.find_elements(
                            By.CLASS_NAME, "fb-dash-form-element")

                        for i in range(len(questions)):
                            input_element = questions[i].find_element(
                                By.CSS_SELECTOR, "input[type='text'], input[type='number'], textarea")
                            resp = self.interface_ia.responder_pergunta(curriculo=curriculo,
                                                                        pergunta=questions[i].text)
                            input_element.send_keys(resp)

            except Exception as e:
                resultados[link] = f"Erro ao acessar a vaga: {str(e)}"
                print(f"Erro ao acessar a vaga {link}: {str(e)}")

            # Pausa entre aplicações para evitar detecção de automação
            time.sleep(random.randint(3, 7))

        return resultados

    def fechar(self) -> None:
        """Fecha o navegador."""
        self.driver.quit()
