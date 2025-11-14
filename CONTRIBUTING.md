# Guia de Contribuição para o Projeto RachAi

Seja bem-vindo(a) à comunidade de desenvolvimento do RachAi! Agradecemos seu interesse em contribuir para este projeto, uma plataforma para divisão de despesas desenvolvida com o framework Django.

O RachAi nasceu como um projeto acadêmico para as disciplinas de Fundamentos de Desenvolvimento de Software e Projetos na CESAR School (turma 2025.1) e tem como objetivo simplificar a forma como amigos gerenciam contas e despesas compartilhadas.

Este guia foi elaborado para orientar você sobre como pode colaborar conosco, seja adicionando novas funcionalidades, corrigindo bugs ou propondo melhorias. Antes de iniciar, recomendamos a leitura atenta deste documento para compreender nosso fluxo de trabalho e as melhores práticas adotadas pela equipe.

## Como Você Pode Contribuir?

Existem diversas maneiras de agregar valor ao RachAi. Você pode:
* Implementar uma funcionalidade que ainda não existe (veja o Backlog no Jira).
* Investigar e solucionar alguma das *issues* abertas no repositório (verifique a aba "Issues" no GitHub).
* Refinar ou otimizar aspectos existentes da aplicação.

Toda contribuição é valiosa e nos ajuda a aprimorar a experiência dos usuários.

## Preparando Seu Ambiente de Contribuição

Para garantir um processo de contribuição organizado e sem conflitos com o código principal, seguimos um fluxo baseado em *forks* e *branches*.

1.  **Faça um "Fork" do Repositório**
    Primeiramente, realize um "Fork" do repositório principal: **[https://github.com/LuccaDangelo/RachAi](https://github.com/LuccaDangelo/RachAi)**. Isso criará uma cópia completa do projeto em sua própria conta do GitHub, permitindo que você trabalhe livremente sem afetar o repositório original.

2.  **Clone o Seu Fork**
    Após criar o fork, clone o seu repositório copiado para a sua máquina local. Utilize o comando `git clone` substituindo `[SuaConta]` pelo seu nome de usuário no GitHub:
    ```bash
    git clone [https://github.com/](https://github.com/)[SuaConta]/RachAi.git
    ```

3.  **Crie uma Nova Branch**
    Com o repositório clonado, navegue até o diretório do projeto e crie uma nova *branch* específica para a sua contribuição. Use um nome descritivo, como `feature/nova-divisao-desigual` ou `fix/correcao-bug-login`:
    ```bash
    cd RachAi
    git checkout -b nome-da-sua-branch
    ```

## Configurando o Ambiente de Desenvolvimento Local

Com o repositório e a branch prontos, o próximo passo é configurar o ambiente de desenvolvimento em sua máquina.

1.  **Crie e Ative um Ambiente Virtual (venv)**
    Recomendamos fortemente o uso de ambientes virtuais. Dentro do diretório do projeto:
    ```bash
    # Crie o ambiente
    python -m venv venv
    ```
    Ative o ambiente virtual:
    * **Windows:** `.\venv\Scripts\activate`
    * **Linux/Mac:** `source venv/bin/activate`

2.  **Instale as Dependências**
    Com o ambiente virtual ativo, instale todas as dependências necessárias listadas no arquivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Aplique as Migrações**
    O Django utiliza migrações para gerenciar o banco de dados. Aplique as migrações para configurar seu banco de dados local (SQLite):
    ```bash
    python manage.py migrate
    ```

4.  **Execute o Servidor**
    Finalmente, inicie o servidor de desenvolvimento do Django:
    ```bash
    python manage.py runserver
    ```
    Agora você está pronto para começar a codificar!

## Garantindo a Qualidade: Executando Testes

Para assegurar que suas alterações não introduzam regressões, é fundamental executar os testes automatizados. O projeto utiliza **Selenium** para testes de sistema (E2E).

**Nota:** Para rodar os testes do Selenium, você pode precisar do [WebDriver](https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/) (como o `chromedriver`) correspondente à versão do seu navegador.

Para executar a suíte de testes integrada ao Django:
```bash
python manage.py test rachais
