import time
import os, tempfile, shutil
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert

User = get_user_model()


class E2EFullFlowTests(StaticLiveServerTestCase):
    """
    Testa o fluxo completo da aplicação RachAi de forma automatizada
    e com pausas visuais entre as etapas (ideal para screencasts).
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_profile = tempfile.mkdtemp(prefix="chrome-prof-")

        opts = webdriver.ChromeOptions()
        opts.add_argument(f"--user-data-dir={cls._tmp_profile}")
        
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        
        opts.add_experimental_option("detach", True) 

        try:
            cls.selenium = webdriver.Chrome(options=opts)
            cls.selenium.implicitly_wait(10) 
        except Exception:
            shutil.rmtree(cls._tmp_profile, ignore_errors=True)
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            cls.selenium.quit()
        finally:
            if cls.__dict__.get("_tmp_profile"):
                shutil.rmtree(cls._tmp_profile, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        
        self.user1_email = 'criador@teste.com'
        self.user1_pass = 'senhaSuperF0rte'
        self.user1 = User.objects.create_user(
            username='criador',
            first_name='Rafael',
            email=self.user1_email,
            password=self.user1_pass
        )

        self.user2_email = 'amigo@teste.com'
        self.user2_pass = 'outraSenha123'
        self.user2 = User.objects.create_user(
            username='amigo.convidado',
            first_name='Amigo',
            email=self.user2_email,
            password=self.user2_pass
        )

    # ===============================================
    # 1. TESTE DE DIVISÃO IGUAL (OK)
    # ===============================================
    def test_fluxo_completo_do_app(self):
        """
        Simula: Login > Criar Grupo > Convidar Amigo > Adicionar Despesa (IGUAL) > Verificar.
        """
        print("\n\n" + "="*50)
        print("INICIANDO TESTE E2E: FLUXO COMPLETO (DIVISÃO IGUAL)")
        print("="*50)
        
        wait = WebDriverWait(self.selenium, 10)
        delay = 3 
        
        print("\n[FLUXO IGUAL - ETAPA 1/5] - Realizando Login...")
        login_url = self.live_server_url + reverse('accounts:login')
        self.selenium.get(login_url)
        
        email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        password_input = self.selenium.find_element(By.NAME, 'password')
        submit_button = self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        email_input.send_keys(self.user1.email)
        time.sleep(delay)
        password_input.send_keys(self.user1_pass)
        time.sleep(delay)
        submit_button.click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Comece criando um grupo')]")))
        print("-> Login realizado com sucesso.")
        time.sleep(delay)

        print("[FLUXO IGUAL - ETAPA 2/5] - Criando Grupo...")
        self.selenium.find_element(By.LINK_TEXT, 'Criar grupo').click()
        nome_grupo_input = wait.until(EC.presence_of_element_located((By.NAME, 'name')))
        nome_grupo_input.send_keys('Viagem de Férias')
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='Criar']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Viagem de Férias')]")))
        print("-> Grupo 'Viagem de Férias' criado com sucesso.")
        time.sleep(delay)

        print("[FLUXO IGUAL - ETAPA 3/5] - Adicionando Participante...")
        email_participante_input = self.selenium.find_element(By.NAME, 'identifier')
        email_participante_input.send_keys(self.user2_email)
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='+ Convidar']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'adicionado(a) com sucesso!')]")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//li[@class='pill' and text()='Amigo']")))
        print(f"-> Participante '{self.user2_email}' adicionado com sucesso.")
        time.sleep(delay)

        print("[FLUXO IGUAL - ETAPA 4/5] - Adicionando Despesa (Divisão Igual)...")
        self.selenium.find_element(By.LINK_TEXT, '+ Adicionar despesa').click()
        description_input = wait.until(EC.presence_of_element_located((By.NAME, 'description')))
        description_input.send_keys('Jantar na Pizzaria')
        time.sleep(delay)
        self.selenium.find_element(By.NAME, 'amount').send_keys('150,00')
        time.sleep(delay)
        select_element = self.selenium.find_element(By.NAME, 'paid_by')
        select = Select(select_element)
        select.select_by_visible_text('Rafael')
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='Salvar']").click()
        
        print("[FLUXO IGUAL - ETAPA 5/5] - Verificando o Resultado...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Jantar na Pizzaria')]")))
        page_source = self.selenium.page_source
        self.assertIn('Pago por Rafael', page_source)
        self.assertIn('R$ 150,00', page_source)
        print("-> Despesa de R$ 150,00 adicionada e verificada com sucesso.")
        summary_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'balance-summary')))
        summary_text = summary_div.text
        self.assertIn('a receber', summary_text)
        self.assertIn('R$ 75,00', summary_text)
        self.assertIn('a pagar', summary_text)
        print("-> Balanço de saldos (Igual) verificado com sucesso.")
        time.sleep(delay)
        print("\n--> Teste de DIVISÃO IGUAL concluído com sucesso!")


    # ========================================================
    # 2. TESTE DE DIVISÃO POR PORCENTAGEM (COM CORREÇÃO)
    # ========================================================
    def test_fluxo_divisao_porcentagem(self):
        """
        Simula: Login > Criar Grupo > Convidar Amigo > Adicionar Despesa (PORCENTAGEM) > Verificar.
        """
        print("\n\n" + "="*50)
        print("INICIANDO TESTE E2E: DIVISÃO POR PORCENTAGEM")
        print("="*50)
        
        wait = WebDriverWait(self.selenium, 10)
        delay = 3 
        
        print("\n[FLUXO % - ETAPA 1/5] - Realizando Login...")
        login_url = self.live_server_url + reverse('accounts:login')
        self.selenium.get(login_url)
        email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        email_input.send_keys(self.user1.email)
        self.selenium.find_element(By.NAME, 'password').send_keys(self.user1_pass)
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Comece criando um grupo')]")))
        print("-> Login realizado com sucesso.")
        time.sleep(delay)

        print("[FLUXO % - ETAPA 2/5] - Criando Grupo...")
        self.selenium.find_element(By.LINK_TEXT, 'Criar grupo').click()
        nome_grupo_input = wait.until(EC.presence_of_element_located((By.NAME, 'name')))
        nome_grupo_input.send_keys('Churrasco 60/40') 
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='Criar']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Churrasco 60/40')]")))
        print("-> Grupo 'Churrasco 60/40' criado com sucesso.")
        time.sleep(delay)

        print("[FLUXO % - ETAPA 3/5] - Adicionando Participante...")
        self.selenium.find_element(By.NAME, 'identifier').send_keys(self.user2_email)
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='+ Convidar']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'adicionado(a) com sucesso!')]")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//li[@class='pill' and text()='Amigo']")))
        print(f"-> Participante '{self.user2_email}' adicionado com sucesso.")
        time.sleep(delay)

        print("[FLUXO % - ETAPA 4/5] - Adicionando Despesa por PORCENTAGEM...")
        self.selenium.find_element(By.LINK_TEXT, '+ Adicionar despesa').click()
        description_input = wait.until(EC.presence_of_element_located((By.NAME, 'description')))
        description_input.send_keys('Carnes do Churrasco')
        time.sleep(delay)
        self.selenium.find_element(By.NAME, 'amount').send_keys('200,00')
        time.sleep(delay)
        select_element = self.selenium.find_element(By.NAME, 'paid_by')
        select_payer = Select(select_element)
        select_payer.select_by_visible_text('Rafael') 
        time.sleep(delay)
        
        split_method_dropdown = Select(wait.until(
            EC.element_to_be_clickable((By.NAME, 'split_method'))
        ))
        split_method_dropdown.select_by_visible_text('Dividir por porcentagem (%)')
        print("-> Método 'Dividir por porcentagem (%)' selecionado.")
        time.sleep(delay)

        
        try:
            perc_input_user1 = wait.until(EC.visibility_of_element_located(
                (By.NAME, f'split_perc_{self.user1.id}')
            ))
            perc_input_user2 = self.selenium.find_element(By.NAME, f'split_perc_{self.user2.id}')
        except Exception as e:
            print(f"Erro ao encontrar os campos de input: {e}")
            self.fail("Não foi possível localizar os campos de porcentagem.")

 
        self.selenium.execute_script("arguments[0].value = '60.0';", perc_input_user1)
        print(f"-> [JS] Input User 1 ({self.user1.id}): 60.0%")
        time.sleep(1) 

        self.selenium.execute_script("arguments[0].value = '40.0';", perc_input_user2)
        print(f"-> [JS] Input User 2 ({self.user2.id}): 40.0%")
    
        self.selenium.execute_script("arguments[0].dispatchEvent(new Event('change'));", perc_input_user1)
        self.selenium.execute_script("arguments[0].dispatchEvent(new Event('change'));", perc_input_user2)
        
        print("-> Valores injetados e eventos 'change' disparados.")
        time.sleep(delay) 
        

        self.selenium.find_element(By.XPATH, "//button[text()='Salvar']").click()
        
        print("[FLUXO % - ETAPA 5/5] - Verificando o Resultado...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Carnes do Churrasco')]")))
        page_source = self.selenium.page_source
        self.assertIn('Pago por Rafael', page_source)
        self.assertIn('R$ 200,00', page_source) 
        print("-> Despesa de R$ 200,00 (Pago por Rafael) verificada.")
        time.sleep(delay)
        
        summary_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'balance-summary')))
        summary_text = summary_div.text
        self.assertIn('R$ 80,00', summary_text) 
        self.assertIn('Rafael', summary_text)
        self.assertIn('a receber', summary_text)
        self.assertIn('Amigo', summary_text)
        self.assertIn('a pagar', summary_text)
        print("-> Balanço de saldos (60/40) verificado com sucesso.")
        time.sleep(delay)
        print("\n--> Teste de DIVISÃO PORCENTAGEM concluído com sucesso!")
        
        
    # ========================================================
    # 3. TESTE DE DIVISÃO POR VALOR EXATO (OK)
    # ========================================================
    def test_fluxo_divisao_valor_exato(self):
        """
        Simula: Login > Criar Grupo > Convidar Amigo > Adicionar Despesa (VALOR EXATO) > Verificar.
        """
        print("\n\n" + "="*50)
        print("INICIANDO TESTE E2E: DIVISÃO POR VALOR EXATO")
        print("="*50)
        
        wait = WebDriverWait(self.selenium, 10)
        delay = 3 
        
        print("\n[FLUXO VALOR - ETAPA 1/5] - Realizando Login...")
        login_url = self.live_server_url + reverse('accounts:login')
        self.selenium.get(login_url)
        email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        email_input.send_keys(self.user1.email)
        self.selenium.find_element(By.NAME, 'password').send_keys(self.user1_pass)
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Comece criando um grupo')]")))
        print("-> Login realizado com sucesso.")
        time.sleep(delay)

        print("[FLUXO VALOR - ETAPA 2/5] - Criando Grupo...")
        self.selenium.find_element(By.LINK_TEXT, 'Criar grupo').click()
        nome_grupo_input = wait.until(EC.presence_of_element_located((By.NAME, 'name')))
        nome_grupo_input.send_keys('Mercado 100/50') 
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='Criar']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Mercado 100/50')]")))
        print("-> Grupo 'Mercado 100/50' criado com sucesso.")
        time.sleep(delay)

        print("[FLUXO VALOR - ETAPA 3/5] - Adicionando Participante...")
        self.selenium.find_element(By.NAME, 'identifier').send_keys(self.user2_email)
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='+ Convidar']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'adicionado(a) com sucesso!')]")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//li[@class='pill' and text()='Amigo']")))
        print(f"-> Participante '{self.user2_email}' adicionado com sucesso.")
        time.sleep(delay)

        print("[FLUXO VALOR - ETAPA 4/5] - Adicionando Despesa por VALOR EXATO...")
        self.selenium.find_element(By.LINK_TEXT, '+ Adicionar despesa').click()
        description_input = wait.until(EC.presence_of_element_located((By.NAME, 'description')))
        description_input.send_keys('Compras do Mercado')
        time.sleep(delay)
        self.selenium.find_element(By.NAME, 'amount').send_keys('150,00')
        time.sleep(delay)
        select_element = self.selenium.find_element(By.NAME, 'paid_by')
        select_payer = Select(select_element)
        select_payer.select_by_visible_text('Amigo') 
        time.sleep(delay)
        
        split_method_dropdown = Select(wait.until(
            EC.element_to_be_clickable((By.NAME, 'split_method'))
        ))
        split_method_dropdown.select_by_visible_text('Dividir por valores exatos (R$)')
        print("-> Método 'Dividir por valores exatos (R$)' selecionado.")
        time.sleep(delay) 

        

        valor_input_user1 = wait.until(EC.visibility_of_element_located(
            (By.NAME, f'split_user_{self.user1.id}')
        ))
        valor_input_user1.clear() 
        valor_input_user1.send_keys('100,00')
        print(f"-> Input User 1 ({self.user1.id}): 100,00")
        time.sleep(delay) 

        valor_input_user2 = self.selenium.find_element(By.NAME, f'split_user_{self.user2.id}')
        valor_input_user2.clear() 
        valor_input_user2.send_keys('50,00')
        print(f"-> Input User 2 ({self.user2.id}): 50,00")
        time.sleep(delay)
        
        self.selenium.find_element(By.XPATH, "//button[text()='Salvar']").click()
        
        print("[FLUXO VALOR - ETAPA 5/5] - Verificando o Resultado...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Compras do Mercado')]")))
        page_source = self.selenium.page_source
        self.assertIn('Pago por Amigo', page_source)
        self.assertIn('R$ 150,00', page_source) 
        print("-> Despesa de R$ 150,00 (Pago por Amigo) verificada.")
        time.sleep(delay)
        
        summary_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'balance-summary')))
        summary_text = summary_div.text
        self.assertIn('R$ 100,00', summary_text) 
        self.assertIn('Rafael', summary_text)
        self.assertIn('a pagar', summary_text)
        self.assertIn('Amigo', summary_text)
        self.assertIn('a receber', summary_text)
        print("-> Balanço de saldos (100/50) verificado com sucesso.")
        time.sleep(delay)
        print("\n--> Teste de DIVISÃO VALOR EXATO concluído com sucesso!")


    # ========================================================
    # 4. TESTE: MARCAR DÍVIDA COMO PAGA
    # ========================================================
    def test_marcar_divida_como_paga(self):
        """
        Fluxo: criar grupo, adicionar amigo, criar despesa (divisão igual),
        verificar que o Amigo deve, logar como Amigo, clicar em Pagar
        e checar que a dívida some das pendentes e entra em Quitadas.
        """
        print("\n\n" + "="*50)
        print("INICIANDO TESTE E2E: MARCAR DÍVIDA COMO PAGA")
        print("="*50)

        wait = WebDriverWait(self.selenium, 10)
        delay = 3

        print("[PAGAMENTO - ETAPA 1/10] - Realizando Login (Rafael)...")
        login_url = self.live_server_url + reverse('accounts:login')
        self.selenium.get(login_url)
        email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        email_input.send_keys(self.user1.email)
        self.selenium.find_element(By.NAME, 'password').send_keys(self.user1_pass)
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Comece criando um grupo')]")))
        print("-> Login realizado com sucesso.")
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 2/10] - Criando Grupo...")
        self.selenium.find_element(By.LINK_TEXT, 'Criar grupo').click()
        nome_grupo_input = wait.until(EC.presence_of_element_located((By.NAME, 'name')))
        nome_grupo_input.send_keys('Grupo Pagamento')
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='Criar']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Grupo Pagamento')]")))
        print("-> Grupo 'Grupo Pagamento' criado com sucesso.")
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 3/10] - Adicionando Participante...")
        self.selenium.find_element(By.NAME, 'identifier').send_keys(self.user2_email)
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='+ Convidar']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'adicionado(a) com sucesso!')]")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//li[@class='pill' and text()='Amigo']")))
        print(f"-> Participante '{self.user2_email}' adicionado com sucesso.")
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 4/10] - Adicionando Despesa...")
        self.selenium.find_element(By.LINK_TEXT, '+ Adicionar despesa').click()
        description_input = wait.until(EC.presence_of_element_located((By.NAME, 'description')))
        description_input.send_keys('Conta do Bar')
        time.sleep(delay)
        self.selenium.find_element(By.NAME, 'amount').send_keys('100,00')
        time.sleep(delay)
        select_element = self.selenium.find_element(By.NAME, 'paid_by')
        Select(select_element).select_by_visible_text('Rafael')
        time.sleep(delay)

        self.selenium.find_element(By.XPATH, "//button[text()='Salvar']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Conta do Bar')]")))
        print("-> Despesa 'Conta do Bar' (R$ 100,00) adicionada.")
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 5/10] - Verificando dívida do Amigo no resumo...")
        summary_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'balance-summary')))
        summary_text = summary_div.text
        self.assertIn('Amigo', summary_text)
        self.assertIn('a pagar', summary_text)
        self.assertIn('R$ 50,00', summary_text)
        print("-> Dívida de R$ 50,00 (Amigo) verificada no resumo.")
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 6/10] - Fazendo logout do Rafael...")
        self.selenium.find_element(By.LINK_TEXT, 'Sair').click()
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 7/10] - Fazendo login com o Amigo...")
        login_url = self.live_server_url + reverse('accounts:login')
        self.selenium.get(login_url)
        email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        email_input.send_keys(self.user2_email)
        self.selenium.find_element(By.NAME, 'password').send_keys(self.user2_pass)
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Seus Grupos') or contains(text(), 'Comece criando um grupo')]")))
        print("-> Login do Amigo realizado com sucesso.")
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 8/10] - Navegando até o grupo 'Grupo Pagamento'...")
        self.selenium.find_element(By.LINK_TEXT, 'Grupo Pagamento').click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Conta do Bar')]")))
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 9/10] - Clicando em 'Pagar' na lista de dívidas pendentes...")
        
        try:
            tab_pendentes = self.selenium.find_element(By.ID, 'tab-pendentes')
            if not tab_pendentes.is_selected():
                tab_pendentes.click()
                time.sleep(1)
        except:
            pass
        
        pagar_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class,'debts-panel--pending')]//button[@class='btn-tertiary' and normalize-space(text())='Pagar']")
            )
        )
        
        pagar_btn.click()
        time.sleep(1)
        
        try:
            alert = Alert(self.selenium)
            alert.accept()
            print("-> Alert de confirmação aceito.")
        except:
            print("-> Nenhum alert encontrado (pode já ter sido processado).")
        
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 10/10] - Aguardando processamento do pagamento...")
        time.sleep(delay)

        print("[PAGAMENTO - ETAPA 11/10] - Verificando que dívida sumiu das pendentes...")
        self.selenium.find_element(By.ID, 'tab-pendentes').click()
        time.sleep(1)
        pending_panel = self.selenium.find_element(By.CSS_SELECTOR, '.debts-panel--pending')
        pending_html = pending_panel.get_attribute('innerText')
        
        if 'Nenhuma pendência' in pending_html:
            print("-> Confirmado: 'Nenhuma pendência no momento.'")
        else:
            self.assertNotIn('R$ 50,00', pending_html) or self.assertIn('Nenhuma pendência', pending_html)
            print("-> Dívida de R$ 50,00 não aparece mais nas pendentes.")

        print("[PAGAMENTO - ETAPA 12/10] - Verificando que pagamento aparece em quitadas...")
        self.selenium.find_element(By.ID, 'tab-quitadas').click()
        time.sleep(1)
        paid_panel = self.selenium.find_element(By.CSS_SELECTOR, '.debts-panel--paid')
        paid_html = paid_panel.get_attribute('innerText')
        self.assertIn('R$ 50,00', paid_html)
        self.assertIn('Rafael', paid_html)
        print("-> Pagamento de R$ 50,00 para Rafael aparece na aba de quitadas.")

        print("\n--> Teste de MARCAR DÍVIDA COMO PAGA concluído com sucesso!")