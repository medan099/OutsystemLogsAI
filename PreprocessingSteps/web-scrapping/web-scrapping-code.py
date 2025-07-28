# 📦 Importation des modules nécessaires
import time
import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import gridfs

# 🧭 Initialisation du navigateur Chrome en mode headless (sans interface graphique)
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)  # Attente maximale de 10 secondes pour les éléments

# 🔌 Connexion à MongoDB et initialisation de GridFS pour stocker les images
client = MongoClient("mongodb://localhost:27017/")
db = client["outsystems_forum_db"]
forum_collection = db["outsystems_forum"]
fs = gridfs.GridFS(db)

# 🍪 Fonction pour fermer la bannière des cookies si elle est présente
def close_cookie_banner():
    try:
        cookie_banner = wait.until(EC.presence_of_element_located((By.ID, "onetrust-policy-text")))
        accept_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        accept_button.click()
        print("✅ Cookie banner closed.")
        time.sleep(2)  # Attente après fermeture
    except:
        print("ℹ️ No cookie banner found.")

# 🖼️ Fonction pour extraire texte et images à partir d’un élément HTML
def extract_text_and_images(element):
    text_with_images = []
    image_references = []

    paragraphs = element.find_elements(By.TAG_NAME, "p")  # Recherche de tous les paragraphes

    for i, p in enumerate(paragraphs):
        img = p.find_elements(By.TAG_NAME, "img")
        if img:
            img_url = img[0].get_attribute("src")  # Récupère le lien de l’image

            # 📥 Téléchargement et stockage de l’image dans MongoDB (GridFS)
            try:
                response = requests.get(img_url)
                if response.status_code == 200:
                    image_id = fs.put(BytesIO(response.content), filename=f"image_{i}.jpg")
                    text_with_images.append(f"[Image_{i}]")  # Remplace l’image par un placeholder
                    image_references.append(str(image_id))  # Stocke l’ID Mongo
            except Exception as e:
                print(f"❌ Error downloading image: {e}")
        else:
            text_with_images.append(p.text.strip())  # Ajoute le texte s'il n'y a pas d’image

    return "\n\n".join(text_with_images), image_references

# 🌐 Lancement de la première page du forum
page_number = 1
driver.get("https://www.outsystems.com/forums/")
time.sleep(3)
close_cookie_banner()  # Fermeture éventuelle de la bannière cookie

# 🔁 Boucle principale de scraping des pages
while True:
    print(f"📄 Scraping page {page_number}...")

    # 📌 Extraction des titres de posts et liens vers les pages de discussion
    problems = driver.find_elements(By.CSS_SELECTOR, "a.text-neutral-8")

    for problem in problems:
        problem_title = problem.text
        problem_url = problem.get_attribute("href")

        # 🧭 Ouvre chaque post dans un nouvel onglet
        driver.execute_script("window.open(arguments[0]);", problem_url)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(2)

        # 📝 Extraction de la description du problème
        try:
            description_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.margin-top-m.fr-view")))
            description_text, description_images = extract_text_and_images(description_element)
            problem_description = {"text": description_text, "images": description_images}
        except:
            problem_description = {"text": "No description found", "images": []}

        # 💡 Extraction des solutions proposées
        solutions = []
        try:
            solution_elements = driver.find_elements(By.CSS_SELECTOR, "div.image-zoom")
            for j, solution in enumerate(solution_elements):
                solution_text, solution_images = extract_text_and_images(solution)
                solutions.append({"text": solution_text, "images": solution_images})
        except:
            solutions.append({"text": "No solutions found", "images": []})

        # 💾 Sauvegarde du post dans la base de données MongoDB
        forum_collection.insert_one({
            "title": problem_title,
            "url": problem_url,
            "description": problem_description,
            "solutions": solutions
        })

        print(f"✅ Saved: {problem_title}")
        driver.close()  # Ferme l'onglet courant
        driver.switch_to.window(driver.window_handles[0])  # Retour à la page principale

    # 🔄 Recherche et clic sur le bouton "Next" pour passer à la page suivante
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "a.ListNavigation_Next")
        if next_button.is_displayed():
            next_button.click()
            page_number += 1
            time.sleep(3)
            close_cookie_banner()  # Ferme à nouveau la bannière si elle réapparaît
        else:
            break
    except Exception as e:
        print(f"❌ Error finding next button: {e}")
        break

# 🛑 Fermeture du navigateur à la fin du scraping
driver.quit()

print("🎉 Scraping complete! All data saved to MongoDB.")
