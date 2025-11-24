"""
Created on Sun Nov 23 21:31:12 2025

@author: davihulse
https://github.com/davihulse/rpa_scrap_defesas

"""

# -*- coding: utf-8 -*-

from time import sleep
import csv
import os
import re
import datetime as dt

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup


URL_DEFESAS = "https://defesas.mbx.academy/mba-usp-esalq"


def iniciar_driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")
    service = Service()
    driver = Chrome(service=service, options=options)
    return driver

def acessar_pagina(driver, url):
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

def extrair_defesas(driver):
    sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser", from_encoding="utf-8")

    # cada card de defesa
    cards = soup.select("div.overflow-hidden.rounded-sm.bg-ctx-layout-surface")

    defesas = []

    for i, card in enumerate(cards, start=1):
        # Curso
        curso_el = card.select_one("div.at-flex p")
        curso = curso_el.get_text(strip=True) if curso_el else ""
        curso = " ".join(curso.split())

        # Título
        titulo_el = card.select_one("h4")
        titulo = titulo_el.get_text(strip=True) if titulo_el else ""
        titulo = " ".join(titulo.split())

        # Nome do aluno
        aluno_el = card.select_one("p.text-xxs.font-bold")
        aluno = aluno_el.get_text(strip=True) if aluno_el else ""
        aluno = " ".join(aluno.split())
        
        # Data e hora
        datahora_el = card.select_one("p.text-xxxs.font-bold.text-ctx-content-base")
        datahora_txt = datahora_el.get_text(strip=True) if datahora_el else ""
        datahora_txt = " ".join(datahora_txt.split())

        # separa data e hora com regex
        m_data = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", datahora_txt)
        m_hora = re.search(r"(\d{2}h\d{2})", datahora_txt)

        data_defesa = m_data.group(1) if m_data else ""
        hora_defesa = m_hora.group(1) if m_hora else ""
        
        # ---- PRINT
        print(f"[{i}] {data_defesa} {hora_defesa} | {aluno}")

        defesas.append(
            {
                "curso": curso,
                "titulo": titulo,
                "aluno": aluno,
                "data": data_defesa,
                "hora": hora_defesa,
                "datahora_bruto": datahora_txt,
            }
        )

    return defesas

def salvar_csv(defesas):
    if not defesas:
        print("Nenhuma defesa encontrada para salvar.")
        return

    pasta = "Arquivos"
    os.makedirs(pasta, exist_ok=True)

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"defesas_mba_usp_esalq_{timestamp}.csv"
    caminho_csv = os.path.join(pasta, nome_arquivo)

    campos = ["curso", "titulo", "aluno", "data", "hora", "datahora_bruto"]

    with open(caminho_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(defesas)

    print(f"Arquivo CSV salvo em: {caminho_csv}")

def salvar_csv_incremental(defesas, caminho_csv):
    if not defesas:
        return

    campos = ["curso", "titulo", "aluno", "data", "hora", "datahora_bruto"]

    escrever_header = not os.path.exists(caminho_csv) or os.path.getsize(caminho_csv) == 0

    with open(caminho_csv, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        if escrever_header:
            writer.writeheader()
        writer.writerows(defesas)

def adicionar_aviso_final(caminho_csv):
    aviso = (
        "\n"
        "Criado pelo aluno DSA 241: Davi Brandeburgo Hulse "
        "Linkedin: https://www.linkedin.com/in/davihulse/pt/ "
        "Código utilizado encontra-se em: https://github.com/davihulse/rpa_scrap_defesas "
    )

    with open(caminho_csv, "a", encoding="utf-8-sig") as f:
        f.write(aviso)

def main():
    driver = iniciar_driver()
    try:
        acessar_pagina(driver, URL_DEFESAS)
        
        # 1) Abrir dropdown datas
        seletor_datas = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "(//button[@role='combobox'])[2]")
            )
        )
        driver.execute_script("arguments[0].click();", seletor_datas)
        sleep(1)
        
        # 2) Capturar todas opções de data
        opcoes_data = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[@role='option']")
            )
        )
        lista_datas = [el.text.strip() for el in opcoes_data]
        
        # Fechar dropdown (clicando fora)
        driver.execute_script("arguments[0].click();", seletor_datas)
        sleep(1)
        
        print("\nDatas encontradas:", lista_datas)

        # Arquivo consolidado
        pasta = "Arquivos"
        os.makedirs(pasta, exist_ok=True)
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"defesas_mba_usp_esalq_{timestamp}.csv"
        caminho_csv = os.path.join(pasta, nome_arquivo)

        for data_texto in lista_datas:
            print(f"\n🔵 Processando data: {data_texto}")
            max_tentativas = 3
            tentativas = 0

            while True:
                tentativas += 1
                print(f"   → Tentativa {tentativas} para {data_texto}")

                # garantir que o seletor de datas esteja aberto
                seletor_datas = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "(//button[@role='combobox'])[2]"))
                )
                estado = seletor_datas.get_attribute("aria-expanded")
                if estado == "false":
                    driver.execute_script("arguments[0].click();", seletor_datas)
                    sleep(0.5)

                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@role='option']"))
                )
                opcoes = driver.find_elements(By.XPATH, "//div[@role='option']")

                opcao = None
                for el in opcoes:
                    if el.text.strip() == data_texto:
                        opcao = el
                        break

                if opcao is None:
                    print(f"⚠️ Data não encontrada no dropdown: {data_texto}")
                    break

                driver.execute_script("arguments[0].click();", opcao)
                sleep(1)

                # Selecionar "Todos os horários"
                seletor_horario = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "(//button[@role='combobox'])[3]"))
                )
                driver.execute_script("arguments[0].click();", seletor_horario)
                sleep(0.5)

                opcao_todos = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//div[@role='option' and contains(., 'Todos os horários')]")
                    )
                )
                driver.execute_script("arguments[0].click();", opcao_todos)
                sleep(1)

                # carregar todos os cards usando "Ver mais"
                while True:
                    try:
                        botao = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//button[contains(., 'Ver mais')]")
                            )
                        )
                    except:
                        break

                    cards_antes = len(driver.find_elements(
                        By.CSS_SELECTOR,
                        "div.overflow-hidden.rounded-sm.bg-ctx-layout-surface"
                    ))

                    try:
                        driver.execute_script("arguments[0].click();", botao)
                    except:
                        break

                    cards_depois = cards_antes
                    for _ in range(3):
                        sleep(1)
                        cards_depois = len(driver.find_elements(
                            By.CSS_SELECTOR,
                            "div.overflow-hidden.rounded-sm.bg-ctx-layout-surface"
                        ))
                        if cards_depois > cards_antes:
                            break

                    if cards_depois <= cards_antes:
                        break

                # extrai só daquela data
                defesas_dia = extrair_defesas(driver)

                if not defesas_dia:
                    print(f"   ⚠ Nenhum card de defesa encontrado para o dia {data_texto}.")
                    if tentativas >= max_tentativas:
                        print(f"   ❗ Máximo de tentativas atingido para {data_texto}. Salvando mesmo assim (lista vazia).")
                        break
                    else:
                        print("   ↻ Recarregando dados da data...")
                        continue

                horas = [d.get("hora", "") for d in defesas_dia if d.get("hora")]
                tem_2030 = "20h30" in horas
                ultima_hora = max(horas) if horas else "nenhuma"

                # VERIFICAÇÃO DO 20h30
                if tem_2030:
                    print(f"   ✔ Defesa das 20h30 encontrada para {data_texto}. Último horário: {ultima_hora}")
                    salvar_csv_incremental(defesas_dia, caminho_csv)
                    break
                                
                # COLETAR HORÁRIO POR HORÁRIO QUANDO NÃO CONSEGUE EXTRAIR TUDO
                                
                print(f"   ⚠ Não encontrou 20h30. Iniciando extração por horário para {data_texto}...")
                
                sleep(1)
                
                # --- Abrir dropdown de horários ---
                seletor_horario = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "(//button[@role='combobox'])[3]"))
                )
                driver.execute_script("arguments[0].click();", seletor_horario)
                sleep(1)
                
                # --- Capturar todos os horários disponíveis ---
                lista_opcoes_horario = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@role='option']"))
                )
                
                horarios = [el.text.strip() for el in lista_opcoes_horario if el.text.strip()]
                print(f"   → Horários encontrados: {horarios}")
                
                # extrair agora horário por horário
                defesas_dia_completa = []
                
                for horario in horarios:
                    print(f"      → Extraindo horário: {horario}")
                
                    # reabrir dropdown
                    seletor_horario = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "(//button[@role='combobox'])[3]"))
                    )
                    driver.execute_script("arguments[0].click();", seletor_horario)
                    sleep(0.5)
                
                    # selecionar o horário desejado
                    item_horario = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, f"//div[@role='option' and contains(., '{horario}')]")
                        )
                    )
                    driver.execute_script("arguments[0].click();", item_horario)
                    sleep(1)
                
                    # carregar TODOS os cards desse horário ; "Ver mais"
                    while True:
                        try:
                            botao = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//button[contains(., 'Ver mais')]")
                                )
                            )
                        except:
                            # não há botão "Ver mais" visível
                            break
                
                        cards_antes = len(driver.find_elements(
                            By.CSS_SELECTOR,
                            "div.overflow-hidden.rounded-sm.bg-ctx-layout-surface"
                        ))
                
                        try:
                            driver.execute_script("arguments[0].click();", botao)
                        except:
                            break
                
                        cards_depois = cards_antes
                        for _ in range(3):
                            sleep(1)
                            cards_depois = len(driver.find_elements(
                                By.CSS_SELECTOR,
                                "div.overflow-hidden.rounded-sm.bg-ctx-layout-surface"
                            ))
                            if cards_depois > cards_antes:
                                break
                
                        # se depois de tentar não entrou card novo, encerra
                        if cards_depois <= cards_antes:
                            break
                
                    # agora extrai os cards desse horário já com tudo carregado
                    lote = extrair_defesas(driver)
                    defesas_dia_completa.extend(lote)
                    
                    print(f"      → Extraindo horário: {horario}")
                
                    # reabrir dropdown (sempre precisa)
                    seletor_horario = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "(//button[@role='combobox'])[3]"))
                    )
                    driver.execute_script("arguments[0].click();", seletor_horario)
                    sleep(0.5)
                
                    # selecionar o horário desejado
                    item_horario = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[@role='option' and contains(., '{horario}')]"))
                    )
                    driver.execute_script("arguments[0].click();", item_horario)
                    sleep(1)
                                
                    lote = extrair_defesas(driver)
                    defesas_dia_completa.extend(lote)
                
                # eliminar duplicatas (mesmo horário pode repetir)
                # manter curso/titulo/aluno como chave
                vis = set()
                sem_dupes = []
                for d in defesas_dia_completa:
                    chave = (d["curso"], d["titulo"], d["aluno"], d["data"], d["hora"])
                    if chave not in vis:
                        vis.add(chave)
                        sem_dupes.append(d)
                
                print(f"   ✔ Extração por horário concluída. Total de itens: {len(sem_dupes)}")
                
                salvar_csv_incremental(sem_dupes, caminho_csv)
                break

        print(f"\n✅ Arquivo consolidado salvo em: {caminho_csv}")
        
        adicionar_aviso_final(caminho_csv)
        print("📌 Aviso final inserido no CSV.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
