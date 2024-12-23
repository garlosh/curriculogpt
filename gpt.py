import openai
import time
from typing import Optional

class GPTClient:
    def __init__(self, api_key: str, modelo: str = "text-davinci-003", max_tokens: int = 1500, temperatura: float = 0.7):
        """
        Inicializa o cliente da API do ChatGPT com configurações padrão.
        
        :param api_key: A chave de API do OpenAI
        :param modelo: O modelo a ser utilizado (padrão: text-davinci-003)
        :param max_tokens: Número máximo de tokens que a API pode gerar na resposta
        :param temperatura: Grau de aleatoriedade na resposta do modelo (0.0 = determinístico, 1.0 = criativo)
        """
        self.api_key = api_key
        openai.api_key = self.api_key
        self.modelo = modelo
        self.max_tokens = max_tokens
        self.temperatura = temperatura
    
    def enviar_prompt(self, prompt: str) -> Optional[str]:
        """
        Envia um prompt para o modelo do ChatGPT e retorna a resposta.
        
        :param prompt: Texto do prompt a ser enviado para a API.
        :return: Resposta do ChatGPT como uma string, ou None em caso de falha.
        """
        try:
            response = openai.Completion.create(
                engine=self.modelo,
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperatura
            )
            
            return response.choices[0].text.strip()
        
        except openai.error.OpenAIError as e:
            print(f"Erro na API do OpenAI: {str(e)}")
            return None

        except Exception as e:
            print(f"Erro inesperado: {str(e)}")
            return None
    
    def ajustar_configuracoes(self, modelo: Optional[str] = None, max_tokens: Optional[int] = None, temperatura: Optional[float] = None):
        """
        Ajusta as configurações da API, como modelo, max_tokens e temperatura.
        
        :param modelo: Modelo a ser utilizado (opcional).
        :param max_tokens: Número máximo de tokens para a resposta (opcional).
        :param temperatura: Temperatura da geração de texto (opcional).
        """
        if modelo:
            self.modelo = modelo
        if max_tokens:
            self.max_tokens = max_tokens
        if temperatura is not None:
            self.temperatura = temperatura

    def retry_on_failure(self, prompt: str, max_retries: int = 3, delay: int = 2) -> Optional[str]:
        """
        Tenta enviar o prompt novamente em caso de falha, até atingir o número máximo de tentativas.
        
        :param prompt: Texto do prompt a ser enviado.
        :param max_retries: Número máximo de tentativas em caso de falha.
        :param delay: Tempo (em segundos) para aguardar entre as tentativas.
        :return: Resposta do ChatGPT ou None se todas as tentativas falharem.
        """
        retries = 0
        while retries < max_retries:
            resposta = self.enviar_prompt(prompt)
            if resposta is not None:
                return resposta
            
            retries += 1
            print(f"Tentativa {retries} falhou. Tentando novamente em {delay} segundos...")
            time.sleep(delay)
        
        print("Número máximo de tentativas atingido. A requisição falhou.")
        return None
