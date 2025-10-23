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
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        cls._tmp_profile = None
        if os.getenv("CI"):
            cls._tmp_profile = tempfile.mkdtemp(prefix="chrome-prof-")
            opts.add_argument(f"--user-data-dir={cls._tmp_profile}")

        cls.selenium = webdriver.Chrome(options=opts)
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.selenium.quit()
        finally:
            if cls.__dict__.get("_tmp_profile"):
                shutil.rmtree(cls._tmp_profile, ignore_errors=True)
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

    def test_fluxo_completo_do_app(self):
        """
        Simula: Login > Criar Grupo > Convidar Amigo > Adicionar Despesa > Verificar.
        """
        wait = WebDriverWait(self.selenium, 10)
        delay = 3
        # --- ETAPA 1: LOGIN ---
        print("\n[ETAPA 1/5] - Realizando Login...")
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

        # --- ETAPA 2: CRIAR GRUPO ---
        print("[ETAPA 2/5] - Criando Grupo...")
        self.selenium.find_element(By.LINK_TEXT, 'Criar grupo').click()
        
        nome_grupo_input = wait.until(EC.presence_of_element_located((By.NAME, 'name')))
        nome_grupo_input.send_keys('Viagem de Férias')
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='Criar']").click()

        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Viagem de Férias')]")))
        print("-> Grupo 'Viagem de Férias' criado com sucesso.")
        time.sleep(delay)

        # --- ETAPA 3: ADICIONAR PARTICIPANTE ---
        print("[ETAPA 3/5] - Adicionando Participante...")
        email_participante_input = self.selenium.find_element(By.NAME, 'identifier')
        email_participante_input.send_keys(self.user2_email)
        time.sleep(delay)
        self.selenium.find_element(By.XPATH, "//button[text()='+ Convidar']").click()

        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'adicionado(a) com sucesso!')]")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//li[@class='pill' and text()='Amigo']")))
        print(f"-> Participante '{self.user2_email}' adicionado com sucesso.")
        time.sleep(delay)

        # --- ETAPA 4: ADICIONAR DESPESA ---
        print("[ETAPA 4/5] - Adicionando Despesa...")
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
        
        # --- ETAPA 5: VERIFICAÇÃO FINAL ---
        print("[ETAPA 5/5] - Verificando o Resultado...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Jantar na Pizzaria')]")))
        
        page_source = self.selenium.page_source
        self.assertIn('Pago por Rafael', page_source)
        self.assertIn('R$ 150,00', page_source)
        print("-> Despesa de R$ 150,00 adicionada e verificada com sucesso.")

        summary_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'balance-summary')))
        self.assertIn('a receber', summary_div.text)
        self.assertIn('a pagar', summary_div.text)
        print("-> Balanço de saldos verificado com sucesso.")
        time.sleep(delay)
        print("\n--> Teste concluído com sucesso!")