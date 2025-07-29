
# Analisador de Relatórios de Hidrômetro

Uma aplicação web desenvolvida para automatizar a consolidação e análise de relatórios diários de consumo de hidrômetros, gerando um resumo mensal detalhado e visual em formato Excel.

---

## ✨ Funcionalidades

- **Interface Web Simples**  
  Uma interface amigável construída com Streamlit que permite o upload de ficheiros de forma intuitiva.

- **Processamento em Lote**  
  Envie um único ficheiro `.ZIP` contendo dezenas de relatórios diários (`.CSV`) para processamento de uma só vez.

- **Cálculos Automatizados**  
  O sistema calcula automaticamente métricas essenciais, incluindo:
  - Consumo diário (baseado na diferença com o dia anterior).
  - Tempo total de bombeamento diário (em horas decimais e no formato `HH:MM`).
  - Percentagem de consumo em relação à outorga diária.

- **Outorga Configurável**  
  O utilizador pode definir o valor da outorga diária diretamente na interface, tornando a análise mais flexível.

- **Relatório Profissional em Excel**  
  Gera um ficheiro `.xlsx` completo com:
  - Tabela de dados diários e totais mensais.
  - Formatação profissional (cabeçalhos coloridos, alinhamento centralizado, formatos numéricos).
  - Um gráfico de colunas comparando o "Consumo Diário" vs. a "Outorga Diária".

---

## 🛠️ Tecnologias Utilizadas

- **Python**: Linguagem principal do projeto.  
- **Streamlit**: Para a criação da interface web interativa.  
- **Pandas**: Para manipulação e análise dos dados.  
- **XlsxWriter**: Para a criação e formatação avançada do ficheiro Excel final, incluindo o gráfico.

---

## 🚀 Instalação e Execução Local

Para executar este projeto no seu ambiente local, siga os passos abaixo.

### Pré-requisitos:
- Python 3.9 ou superior.
- `pip` (gestor de pacotes do Python).

### Passos:

1. **Clone o repositório (ou descarregue os ficheiros):**
   ```bash
   git clone [URL_DO_SEU_REPOSITÓRIO]
   cd [NOME_DA_PASTA_DO_PROJETO]
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   # Criar o ambiente
   python -m venv venv

   # Ativar no Windows
   .\venv\Scripts\activate

   # Ativar no macOS/Linux
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   O projeto requer as bibliotecas listadas no ficheiro `requirements.txt`. Instale todas com:
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute a aplicação:**
   ```bash
   streamlit run app.py
   ```
   A aplicação será aberta automaticamente no seu navegador padrão.

---

## 📄 Como Usar

1. **Reúna os ficheiros:** Junte todos os relatórios diários no formato `.CSV` numa única pasta.  
2. **Crie o ficheiro `.ZIP`:** Comprima todos os ficheiros `.CSV` num único ficheiro `.ZIP`.  
3. **Abra a Aplicação:** Execute o programa conforme as instruções acima.  
4. **Defina a Outorga:** Insira o valor da outorga diária em m³.  
5. **Envie o Ficheiro:** Clique em *"Browse files"* e selecione o seu ficheiro `.ZIP`.  
6. **Descarregue o Relatório:** Aguarde o processamento. No final, clique no botão *"Baixar Resumo em Excel"* para obter o seu relatório consolidado.

---

## 📊 Formato dos Dados de Entrada

Para o correto funcionamento, os ficheiros `.CSV` devem seguir o seguinte formato:

- **Sem Cabeçalho:** A primeira linha do ficheiro já deve ser um registo de dados.
- **Separador:** As colunas devem ser separadas por vírgula (`,`).
- **Estrutura das Colunas:** O programa espera a seguinte estrutura (posições começam em 0):

  - Coluna 1: Data no formato `AAAA/MM/DD`  
  - Coluna 2: Hora no formato `HH:MM:SS`  
  - Coluna 5: Leitura da vazão total (números inteiros)

---

## ⚖️ Licença e Termos de Uso

Este projeto é disponibilizado para uso pessoal e educacional.  
É expressamente proibida a sua utilização para fins lucrativos, revenda, ou integração em produtos comerciais sem a autorização prévia e por escrito do autor.  
Para consultas sobre licenciamento comercial, por favor, entre em contato.

---

## 📂 Estrutura do Projeto

```
├── app.py              # Script principal da aplicação Streamlit
├── requirements.txt    # Lista de dependências Python
└── README.md           # Este ficheiro
```
