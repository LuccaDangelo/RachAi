from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

User = get_user_model()

# ======================================================================
# TESTE DE DIAGNÓSTICO (PROVA QUE O BACKEND FUNCIONA)
# ======================================================================
class ADiagnosticTest(TestCase):
    def test_login_page_loads_without_crashing(self):
        login_url = reverse('accounts:login')
        response = self.client.get(login_url)
        self.assertEqual(response.status_code, 200)


# ======================================================================
# TESTE E2E COM SELENIUM (VERSÃO FINAL E ROBUSTA)
# ======================================================================
class E2EAuthenticationTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = webdriver.Chrome()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.email = 'teste@email.com'
        self.password = 'senhaSuperF0rte'
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password
        )

    def test_fluxo_completo_login_e_logout(self):
        self.selenium.get(f'{self.live_server_url}/accounts/entrar/')

        wait = WebDriverWait(self.selenium, 10)

        try:
            email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
            print("-> Formulário de login encontrado diretamente.")
        except TimeoutException:
            print("-> Página de boas-vindas encontrada. Clicando em 'Entrar'...")
            entrar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Entrar']")))
            entrar_button.click()
            email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))

        password_input = self.selenium.find_element(By.NAME, 'password')
        submit_button = self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]')

        email_input.send_keys(self.email)
        password_input.send_keys(self.password)
        submit_button.click()

        wait.until(EC.url_contains('/home/'))
        main_title = wait.until(
            EC.presence_of_element_located((By.XPATH, "//h1[text()='Comece criando um grupo']"))
        ).text
        self.assertEqual(main_title, "Comece criando um grupo")
        print("-> Login verificado com sucesso.")
        
        logout_link = self.selenium.find_element(By.LINK_TEXT, 'Sair')
        logout_link.click()
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Entrar']")))
        print("-> Logout verificado com sucesso.")