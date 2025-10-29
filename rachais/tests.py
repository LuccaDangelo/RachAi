import time
import os, tempfile, shutil
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

User = get_user_model()


class E2EFullFlowTests(StaticLiveServerTestCase):
    """
    Testa o fluxo completo da aplicação RachAi de forma automatizada
    e com pausas visuais entre as etapas.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_profile = tempfile.mkdtemp(prefix="chrome-prof-")

        opts = webdriver.ChromeOptions()
        opts.add_argument(f"--user-data-dir={cls._tmp_profile}")
        
        # Para rodar "invisível" (sem abrir a janela), descomente a linha abaixo:
        # opts.add_argument("--headless=new") 
        
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        
        # Descomente a linha abaixo se quiser VER o teste rodando
        opts.add_experimental_option("detach", True) 

        try:
            cls.selenium = webdriver.Chrome(options=opts)
            cls.selenium.implicitly_wait(10) 
        except Exception:
            shutil.rmtree(cls._tmp_profile, ignore_errors=True)
            raise

    @classmethod
    def tearDownClass(cls):
        # --- INÍCIO DA CORREÇÃO (Problema 2) ---
        # Removido o bloco 'if' que causava o AttributeError
        try:
            cls.selenium.quit()
        finally:
            if cls.__dict__.get("_tmp_profile"):
                shutil.rmtree(cls._tmp_profile, ignore_errors=True)
        # --- FIM DA CORREÇÃO ---
        super().tearDownClass()

    def setUp(self):
        # Usuário 1
        self.user1_email = 'criador@teste.com'
        self.user1_pass = 'senhaSuperF0rte'
        self.user1 = User.objects.create_user(
            username='criador',
            first_name='Rafael',
            email=self.user1_email,
            password=self.user1_pass
        )

        # Usuário 2 
        self.user2_email = 'amigo@teste.com'
        self.user2_pass = 'outraSenha123'
        self.user2 = User.objects.create_user(
            username='amigo.convidado',
            first_name='Amigo',
            email=self.user2_email,
            password=self.user2_pass
        )

    # ===============================================
    # 1. SEU TESTE ORIGINAL (DIVISÃO IGUAL) - OK
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
    # 2. NOVO TESTE (DIVISÃO POR PORCENTAGEM) - CORRIGIDO
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
        select_payer.select_by_visible_text('Rafael') # user1
        time.sleep(delay)
        
        split_method_dropdown = Select(wait.until(
            EC.element_to_be_clickable((By.NAME, 'split_method'))
        ))
        split_method_dropdown.select_by_visible_text('Dividir por porcentagem (%)')
        print("-> Método 'Dividir por porcentagem (%)' selecionado.")
        time.sleep(delay) 

        # --- INÍCIO DA CORREÇÃO (Problema 1) ---
        
        # 1. Preencher a porcentagem do User 1 (Rafael)
        perc_input_user1 = wait.until(EC.visibility_of_element_located(
            (By.NAME, f'split_perc_{self.user1.id}')
        ))
        perc_input_user1.clear() # Limpa o campo
        perc_input_user1.send_keys('60.0')
        print(f"-> Input User 1 ({self.user1.id}): 60.0%")
        time.sleep(delay) # Pausa para o JS rodar
        
        # 2. Preencher a porcentagem do User 2 (Amigo)
        perc_input_user2 = self.selenium.find_element(By.NAME, f'split_perc_{self.user2.id}')
        perc_input_user2.clear() # Limpa o que o JS preencheu
        perc_input_user2.send_keys('40.0') 
        print(f"-> Input User 2 ({self.user2.id}): 40.0%")
        time.sleep(delay)
        
        # --- FIM DA CORREÇÃO ---
        
        # 3. Salvar
        self.selenium.find_element(By.XPATH, "//button[text()='Salvar']").click()
        
        print("[FLUXO % - ETAPA 5/5] - Verificando o Resultado...")
        # A espera agora DEVE funcionar
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Carnes do Churrasco')]")))
        page_source = self.selenium.page_source
        self.assertIn('Pago por Rafael', page_source)
        self.assertIn('R$ 200,00', page_source) # Valor total
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
    # 3. NOVO TESTE (DIVISÃO POR VALOR EXATO) - CORRIGIDO
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
        select_payer.select_by_visible_text('Amigo') # user2, para variar o pagador
        time.sleep(delay)
        
        split_method_dropdown = Select(wait.until(
            EC.element_to_be_clickable((By.NAME, 'split_method'))
        ))
        split_method_dropdown.select_by_visible_text('Dividir por valores exatos (R$)')
        print("-> Método 'Dividir por valores exatos (R$)' selecionado.")
        time.sleep(delay) 

        # --- INÍCIO DA CORREÇÃO (Problema 1) ---
        
        # 1. Preencher o valor do User 1 (Rafael)
        valor_input_user1 = wait.until(EC.visibility_of_element_located(
            (By.NAME, f'split_user_{self.user1.id}')
        ))
        valor_input_user1.clear() # Limpa o campo
        valor_input_user1.send_keys('100,00')
        print(f"-> Input User 1 ({self.user1.id}): 100,00")
        time.sleep(delay) # Pausa para o JS rodar

        # 2. Preencher o valor do User 2 (Amigo)
        valor_input_user2 = self.selenium.find_element(By.NAME, f'split_user_{self.user2.id}')
        valor_input_user2.clear() # Limpa o que o JS preencheu
        valor_input_user2.send_keys('50,00')
        print(f"-> Input User 2 ({self.user2.id}): 50,00")
        time.sleep(delay)

        # --- FIM DA CORREÇÃO ---
        
        # 3. Salvar
        self.selenium.find_element(By.XPATH, "//button[text()='Salvar']").click()
        
        print("[FLUXO VALOR - ETAPA 5/5] - Verificando o Resultado...")
        # A espera agora DEVE funcionar
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Compras do Mercado')]")))
        page_source = self.selenium.page_source
        self.assertIn('Pago por Amigo', page_source)
        self.assertIn('R$ 150,00', page_source) # Valor total
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