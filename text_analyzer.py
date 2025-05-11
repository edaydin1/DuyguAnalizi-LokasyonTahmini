import google.generativeai as genai
import os

# API anahtarını kullanınız.
GOOGLE_API_KEY = "GOOGLE_API_KEY"

def analyze_transcript(transcript):
    """
    Video transkriptinden lokasyonları ve ilgili cümleleri çıkarır.
    """
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
        
        prompt = f"""
        Aşağıdaki metinden turistik yerleri, tarihi mekanları ve önemli lokasyonları çıkar.
        Her lokasyon için, o lokasyonun geçtiği ilgili cümleyi de belirt.
        Çıktıyı aşağıdaki formatta döndür:
        
        Pantheon: "Bu cümlede Pantheon geçiyor."
        Trevi Çeşmesi: "Bu cümlede Trevi Çeşmesi geçiyor."
        
        Eğer lokasyon için cümle bulunamazsa, lokasyon adının karşısına boş string koy.
        Yanıtı sadece lokasyon ve cümle çiftleri olarak ver, başka açıklama ekleme.
        
        Metin:
        {transcript}
        """
        
        response = model.generate_content(prompt)
        print("API Yanıtı (Transkript):", response.text)
        
        locations = {}
        if response.text:
            for line in response.text.split('\n'):
                line = line.strip()
                if not line or line.startswith('```') or line.startswith('#'):
                    continue
                    
                if ":" in line:
                    try:
                        parts = line.split(":", 1)
                        loc = parts[0].strip()
                        sentence = parts[1].strip().strip('"').strip("'")
                        if loc:  # Boş lokasyon adlarını atla
                            locations[loc] = sentence
                    except Exception as e:
                        print(f"Satır işleme hatası: {e} - Satır: {line}")
                        continue
        
        print("Çıkarılan Lokasyonlar (Transkript):", locations)
        return locations
    except Exception as e:
        print(f"Hata (Transkript Analizi): {e}")
        return {}

def analyze_video_title(title):
    """
    Video başlığından ana lokasyonu çıkarır.
    """
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")

        prompt = f"""
        Bu video başlığından ana şehir veya bölgeyi tespit et:
        {title}

        Sadece şehir/bölge adını döndür (örnek: Roma, Paris, Londra).
        Eğer kesin değilsen boş döndür.
        """

        response = model.generate_content(prompt)
        main_location = response.text.strip() if response.text else None
        print("Ana Lokasyon (Başlık):", main_location)
        return main_location
    except Exception as e:
        print(f"Hata (Başlık Analizi): {e}")
        return None

'''


streamlit run main.py 


'''



