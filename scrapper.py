from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from dataclasses import dataclass, asdict
from typing import List, Optional
import numpy as np
import multiprocessing
import time
from dotenv import load_dotenv, find_dotenv
from os import environ
import json
#import os
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

#Falta adequar isso
def parallelize(funct, iterable, processes = None) -> np.array:
    # Determina o número de núcleos disponíveis
    
    num_nucleos = multiprocessing.cpu_count() - 1 if processes is None else  processes
    
    print(f"Número de núcleos disponíveis: {num_nucleos}")

    resultados = np.array([])
    # Cria um pool de processos que utiliza todos os núcleos
    with multiprocessing.Pool(processes=num_nucleos) as pool:

        # Executa a função 'tarefa' em paralelo para cada número da lista
        for i in pool.imap_unordered(funct, iterable):
            resultados = np.append(resultados, i)

    # Exibe os resultados
    return resultados

# Classe para gerenciar o LinkedIn
class LinkedInBot:
    def __init__(self):
        self.driver:webdriver.Edge = webdriver.Edge()
    
    def login(self, credentials:LinkedInCredentials):
        """Realiza login no LinkedIn."""
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
        #Funções vetoriais
        get_pag_number = np.vectorize(lambda x: np.int16(x.get_attribute('data-test-pagination-page-btn')))
        get_link = np.vectorize(lambda x: x.get_attribute('href'))

        self.driver.get(f"https://www.linkedin.com/jobs/search/?keywords={palavra_chave}&location={localizacao}")
        time.sleep(5)

        # Coleta os links das vagas
        
        pags_root = np.array(self.driver.find_elements(By.XPATH, "//li[@data-test-pagination-page-btn]"))
        n_pags_root = get_pag_number(pags_root)
        links_vagas = np.array([])
        
        #pdb.set_trace()
        max_pag = 25 * np.max(n_pags_root)


        #Não consegue captar todos os links ainda, falta melhorar essa parte
        for i in range(25, 50, 25):
            try:
                #Links
                self.driver.get(f"https://www.linkedin.com/jobs/search/?keywords={palavra_chave}&location={localizacao}&start={i}")
                time.sleep(5)
                #Pega as vagas
                vagas:np.array = np.array(self.driver.find_elements(By.XPATH, "//a[contains(@class, 'job-card-list__title')]"))
                links_pag = get_link(vagas)
                links_vagas = np.concatenate((links_vagas, links_pag))
                
            except:
                continue
            

        return links_vagas

    def aplicar_vaga(self, link_vaga: str, curriculo: str):
        """Aplica em uma vaga específica."""
        self.driver.get(link_vaga)
        time.sleep(5)

        try:
            # Encontra e clica no botão "Candidatar-se"
            aplicar_btn = self.driver.find_element(By.CLASS_NAME, "jobs-apply-button")
            aplicar_btn.click()
            time.sleep(3)

            # Preenche os dados de candidatura, como o currículo
            upload_element = self.driver.find_element(By.NAME, "file-upload-input")
            #upload_element.send_keys(curriculo)  # Caminho para o arquivo do currículo PDF

            # Submete a candidatura
            submit_btn = self.driver.find_element(By.CLASS_NAME, "jobs-apply-form__submit-button")
            submit_btn.click()
            
            print(f"Aplicação concluída para: {link_vaga}")
        except Exception as e:
            print(f"Erro ao aplicar para a vaga: {link_vaga}, erro: {str(e)}")

    def obter_detalhes_vaga(self, link_vaga: str) -> Optional['Vaga']:
        """Navega até a vaga e coleta detalhes, incluindo estilo de trabalho, senioridade e método de apply."""
        self.driver.get(link_vaga)
        time.sleep(5)

        try:
            # Estilo de trabalho (Remoto, Híbrido, Presencial)
            estilo_trabalho = "Indefinido"
            try:
                estilo_trabalho_elem = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Remoto') or contains(text(), 'Híbrido') or contains(text(), 'Presencial')]")
                estilo_trabalho = estilo_trabalho_elem.text
            except:
                pass

            # Nível de senioridade
            nivel_senioridade = "Indefinido"
            try:
                nivel_senioridade_elem = self.driver.find_element(By.XPATH, "//span[@dir and contains(@class, 'job-details-jobs-unified-top-card__job-insight-view-model-secondary')]")
                nivel_senioridade = nivel_senioridade_elem.text
            except:
                pass

            # Método de candidatura (Easy Apply, Apply Externo, ou Apply)
            metodo_apply = "Indefinido"
            try:
                apply_btn_elem = self.driver.find_element(By.CLASS_NAME, "jobs-apply-button").get_attribute("aria-label")
                if apply_btn_elem.lower().find("candidatura") != -1:
                    metodo_apply = "Interno"
                else:
                    metodo_apply = "Externo"
                
            except:
                pass

            # Descrição da vaga
            desc = "Indefinido"
            try:
                self.driver.find_element(By.XPATH, "//button[contains(@class, 'jobs-description__footer-button')]").click() #Não precisa salvar na memória
                desc_elem = self.driver.find_element(By.XPATH, "//*[@id='job-details']/div")
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
            print(f"Erro ao obter detalhes da vaga: {link_vaga}, erro: {str(e)}")
            return None
        

    def fechar(self):
        """Fecha o navegador."""
        self.driver.quit()



# Função principal para executar o fluxo de login, busca e aplicação de vagas
def main():
    # Configurar credenciais
    load_dotenv(find_dotenv(), override = True)
    credentials = LinkedInCredentials(
        email=environ.get("LINKEDIN_USER"),
        password=environ.get("LINKEDIN_PASS")
    )
    
    # Inicializa o bot do LinkedIn
    bot = LinkedInBot()

    try:
        # Login no LinkedIn
        bot.login(credentials)
        
        # Busca vagas de desenvolvedor Python no Brasil
        links_de_vagas = bot.buscar_vagas("Desenvolvedor Python", "Brasil")

        vagas = np.array([])
        # Exibe as vagas encontradas e busca mais detalhes
        #print(f"Nº de links: {len(links_de_vagas)}")
        #Este for pode talvez ser paralelizado em varios browsers
        for link in links_de_vagas: 
            vagas = np.append(vagas, bot.obter_detalhes_vaga(link))
            #if detalhes_vaga:
            #    print(f"Estilo de Trabalho: {detalhes_vaga.estilo_trabalho}")
            #    print(f"Nível de Senioridade: {detalhes_vaga.nivel_senioridade}")
            #    print(f"Método de Apply: {detalhes_vaga.metodo_apply}")
            #    print("-" * 40)

        vagas_dict_list = [asdict(vaga) for vaga in vagas]
        # Salvando como JSON
        with open("vagas.json", "w", encoding="utf-8") as json_file:
            json.dump(vagas_dict_list, json_file, indent=4, ensure_ascii=False)
    finally:
        # Fechar o navegador
        bot.fechar()

# Executa o script principal
if __name__ == "__main__":
    main()