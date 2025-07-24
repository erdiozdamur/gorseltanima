from flask import Flask, render_template, request, jsonify
from transformers import pipeline
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- KATEGORİ YAPISI (ZENGİNLEŞTİRİLMİŞ) ---

# 1. Ana Kategoriler (Değişiklik yok)
ANA_KATEGORILER = [
    "Hotel General View", "Hotel Spa & Wellness Facilities", "Hotel Child and Baby Facilities",
    "Hotel Sport and Entertainment Facilities", "Hotel Food and Beverage Facilities", "Hotel Room",
    "Hotel Meeting and Conference Facilities", "Other"
]

# 2. Alt Kategoriler (Zenginleştirilmiş ve Atmosfer Odaklı)
ALT_KATEGORILER = [
    # --- Genel Otel Görünümleri ---
    "Hotel exterior day shot", "Hotel exterior night shot", "Aerial view of the hotel", "Hotel entrance and driveway",
    "Hotel lobby and reception area", "Hotel building architecture", "Hotel garden and landscape",
    
    # --- Spa & Wellness ---
    "Spa and wellness center", "Massage room or therapy bed", "Sauna", "Turkish bath or Hamam", "Steam room",
    "Indoor swimming pool", "Jacuzzi or hot tub", "Fitness center or gym", "Spa relaxation lounge",
    
    # --- GELİŞTİRİLMİŞ ÇOCUK HAVUZU KATEGORİLERİ ---
    "Shallow kids' pool with colorful play structures and toy figures",
    "Children's water park area with small, themed water slides and splash pads",
    "Playful kids' pool with bright colors, fountains, and inflatable toys",
    "Artificial sandy beach or wave pool designed for children and families",
    
    # --- GELİŞTİRİLMİŞ YETİŞKİN & GENEL KULLANIM HAVUZU KATEGORİLERİ ---
    "Serene infinity pool with a panoramic view for relaxation",
    "Luxury hotel pool with a swim-up bar and submerged loungers",
    "Large, tranquil main swimming pool surrounded by neat sun loungers and cabanas",
    "Geometric lap pool for swimming exercise",
    "Activity or animation pool for hotel entertainment",
    "Large water park with high and fast slides for teens and adults",
    
    # --- Diğer Çocuk & Bebek Tesisleri ---
    "Kids club or indoor playground", "Outdoor children's playground", "Baby cot or crib in a room", "High chairs for babies",
    
    # --- Diğer Spor & Eğlence Tesisleri ---
    "Tennis court", "Basketball or volleyball court", "Beach volleyball", "Water sports like jet ski or parasailing", 
    "Billiards or pool table", "Bowling alley", "Amphitheater or show stage", "Live music or band performance", 
    "Night club or disco",
    
    # --- Yiyecek & İçecek ---
    "Restaurant interior", "Open buffet food display", "A'la carte restaurant dining", "Bar or pub area",
    "Poolside bar", "Beach bar", "Patisserie or cafe with cakes", "Close-up of a food dish", "Cocktail or drink",
    
    # --- Oda ---
    "Hotel room bedroom area", "Hotel suite with living room", "Hotel room bathroom",
    "Hotel room balcony or terrace", "View from the hotel room",
    
    # --- Toplantı & Konferans ---
    "Conference hall or meeting room", "Ballroom for events or weddings", "Business center",
    "Auditorium or theater setup", "Coffee break station"
]


# 3. Kategori Haritası (Yeni kategoriler eklendi)
KATEGORI_HARITASI = {
    "Hotel exterior day shot": "Hotel General View", "Hotel exterior night shot": "Hotel General View",
    "Aerial view of the hotel": "Hotel General View", "Hotel entrance and driveway": "Hotel General View",
    "Hotel lobby and reception area": "Hotel General View", "Hotel building architecture": "Hotel General View",
    "Hotel garden and landscape": "Hotel General View",
    
    "Spa and wellness center": "Hotel Spa & Wellness Facilities", "Massage room or therapy bed": "Hotel Spa & Wellness Facilities",
    "Sauna": "Hotel Spa & Wellness Facilities", "Turkish bath or Hamam": "Hotel Spa & Wellness Facilities",
    "Steam room": "Hotel Spa & Wellness Facilities", "Indoor swimming pool": "Hotel Spa & Wellness Facilities",
    "Jacuzzi or hot tub": "Hotel Spa & Wellness Facilities", "Fitness center or gym": "Hotel Spa & Wellness Facilities",
    "Spa relaxation lounge": "Hotel Spa & Wellness Facilities",
    
    # --- YENİ HARİTA GİRDİLERİ (ÇOCUK) ---
    "Shallow kids' pool with colorful play structures and toy figures": "Hotel Child and Baby Facilities",
    "Children's water park area with small, themed water slides and splash pads": "Hotel Child and Baby Facilities",
    "Playful kids' pool with bright colors, fountains, and inflatable toys": "Hotel Child and Baby Facilities",
    "Artificial sandy beach or wave pool designed for children and families": "Hotel Child and Baby Facilities",
    "Kids club or indoor playground": "Hotel Child and Baby Facilities",
    "Outdoor children's playground": "Hotel Child and Baby Facilities",
    "Baby cot or crib in a room": "Hotel Child and Baby Facilities", "High chairs for babies": "Hotel Child and Baby Facilities",
    
    # --- YENİ HARİTA GİRDİLERİ (GENEL/YETİŞKİN) ---
    "Serene infinity pool with a panoramic view for relaxation": "Hotel Sport and Entertainment Facilities",
    "Luxury hotel pool with a swim-up bar and submerged loungers": "Hotel Sport and Entertainment Facilities",
    "Large, tranquil main swimming pool surrounded by neat sun loungers and cabanas": "Hotel Sport and Entertainment Facilities",
    "Geometric lap pool for swimming exercise": "Hotel Sport and Entertainment Facilities",
    "Activity or animation pool for hotel entertainment": "Hotel Sport and Entertainment Facilities",
    "Large water park with high and fast slides for teens and adults": "Hotel Sport and Entertainment Facilities",
    
    # --- Diğer kategorilerin haritalanması ---
    "Tennis court": "Hotel Sport and Entertainment Facilities", "Basketball or volleyball court": "Hotel Sport and Entertainment Facilities",
    "Beach volleyball": "Hotel Sport and Entertainment Facilities", "Water sports like jet ski or parasailing": "Hotel Sport and Entertainment Facilities",
    "Billiards or pool table": "Hotel Sport and Entertainment Facilities", "Bowling alley": "Hotel Sport and Entertainment Facilities",
    "Amphitheater or show stage": "Hotel Sport and Entertainment Facilities", "Live music or band performance": "Hotel Sport and Entertainment Facilities",
    "Night club or disco": "Hotel Sport and Entertainment Facilities",
    
    "Restaurant interior": "Hotel Food and Beverage Facilities", "Open buffet food display": "Hotel Food and Beverage Facilities",
    "A'la carte restaurant dining": "Hotel Food and Beverage Facilities", "Bar or pub area": "Hotel Food and Beverage Facilities",
    "Poolside bar": "Hotel Food and Beverage Facilities", "Beach bar": "Hotel Food and Beverage Facilities",
    "Patisserie or cafe with cakes": "Hotel Food and Beverage Facilities", "Close-up of a food dish": "Hotel Food and Beverage Facilities",
    "Cocktail or drink": "Hotel Food and Beverage Facilities",
    
    "Hotel room bedroom area": "Hotel Room", "Hotel suite with living room": "Hotel Room",
    "Hotel room bathroom": "Hotel Room", "Hotel room balcony or terrace": "Hotel Room", "View from the hotel room": "Hotel Room",
    
    "Conference hall or meeting room": "Hotel Meeting and Conference Facilities", "Ballroom for events or weddings": "Hotel Meeting and Conference Facilities",
    "Business center": "Hotel Meeting and Conference Facilities", "Auditorium or theater setup": "Hotel Meeting and Conference Facilities",
    "Coffee break station": "Hotel Meeting and Conference Facilities"
}

# --- AKILLI ANALİZ İÇİN YENİ BÖLÜM ---
COCUK_HAVUZU_ANAHTAR_KELIMELER = [
    'kids', 'children', 'play', 'toy', 'colorful', 'shallow',
    'splash', 'themed', 'slide', 'figure', 'inflatable', 'sandy', 'playful'
]

YETISKIN_HAVUZU_ANAHTAR_KELIMELER = [
    'serene', 'tranquil', 'luxury', 'infinity', 'relaxation',
    'lounge', 'cabana', 'panoramic', 'adults', 'submerged', 'bar', 'lap', 'neat'
]
# ----------------------------------------

TAHMIN_LABEL_PROMPTLARI = [f"a photo of a {label}" for label in ALT_KATEGORILER]
PROMPT_TO_LABEL_MAP = {f"a photo of a {label}": label for label in ALT_KATEGORILER}

print("Lokal model yükleniyor...")
LOKAL_MODEL_YOLU = "./clip-model-lokal"
try:
    classifier = pipeline("zero-shot-image-classification", model=LOKAL_MODEL_YOLU, local_files_only=True, device="mps")
except Exception:
    classifier = pipeline("zero-shot-image-classification", model=LOKAL_MODEL_YOLU, local_files_only=True)
print("Lokal model başarıyla yüklendi.")

def akilli_havuz_analizi(predictions):
    """
    Modelin en iyi birkaç tahminini analiz ederek, görselin
    çocuk veya yetişkin havuzu olma olasılığını hesaplar.
    """
    cocuk_skoru = 0.0
    yetiskin_skoru = 0.0

    # Modelin en iyi 3 tahminini analiz et
    for prediction in predictions[:3]:
        label_text = prediction['label'].lower()
        score = prediction['score']

        # Çocuk havuzu anahtar kelimelerini kontrol et
        if any(keyword in label_text for keyword in COCUK_HAVUZU_ANAHTAR_KELIMELER):
            cocuk_skoru += score

        # Yetişkin havuzu anahtar kelimelerini kontrol et
        if any(keyword in label_text for keyword in YETISKIN_HAVUZU_ANAHTAR_KELIMELER):
            yetiskin_skoru += score
            
    toplam_skor = cocuk_skoru + yetiskin_skoru
    if toplam_skor > 0:
        cocuk_olasiligi = cocuk_skoru / toplam_skor
        yetiskin_olasiligi = yetiskin_skoru / toplam_skor
    else:
        cocuk_olasiligi = 0.0
        yetiskin_olasiligi = 0.0

    return {
        "analysis_complete": toplam_skor > 0,
        "child_pool_confidence": round(cocuk_olasiligi, 4),
        "adult_pool_confidence": round(yetiskin_olasiligi, 4)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify_images():
    uploaded_files = request.files.getlist("images")
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({'error': 'Lütfen en az bir görsel seçin.'}), 400

    resim_yollari = []
    for file in uploaded_files:
        if file.filename != '':
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            resim_yollari.append(path)
    
    if not resim_yollari:
        return jsonify({'error': 'Geçerli bir görsel dosyası seçilmedi.'}), 400

    try:
        # Birden fazla resmi tek seferde işlemek için listeyi doğrudan modele veriyoruz.
        tum_sonuclar = classifier(resim_yollari, candidate_labels=TAHMIN_LABEL_PROMPTLARI)
    except Exception as e:
        for path in resim_yollari: os.remove(path)
        return jsonify({'error': f'Model çalıştırılırken bir hata oluştu: {str(e)}'}), 500

    response_data = []
    # tum_sonuclar her bir resim için bir tahmin listesi içeren bir liste döner.
    for resim_yolu, sonuclar_tek_resim in zip(resim_yollari, tum_sonuclar):
        
        # --- YENİ EKLENEN AKILLI ANALİZ ÇAĞRISI ---
        havuz_analizi_sonucu = akilli_havuz_analizi(sonuclar_tek_resim)
        # -------------------------------------------

        image_predictions = []
        for prediction in sonuclar_tek_resim[:3]:
            tahmin_edilen_prompt = prediction['label']
            tahmin_skoru = prediction['score']
            tahmin_edilen_alt_kategori = PROMPT_TO_LABEL_MAP.get(tahmin_edilen_prompt, "N/A")
            tahmin_edilen_ana_kategori = KATEGORI_HARITASI.get(tahmin_edilen_alt_kategori, "Other")
            image_predictions.append({
                "main_category": tahmin_edilen_ana_kategori,
                "sub_category": tahmin_edilen_alt_kategori,
                "score": round(tahmin_skoru, 4)
            })
        
        response_data.append({
            'filename': os.path.basename(resim_yolu),
            'predictions': image_predictions,
            'pool_type_analysis': havuz_analizi_sonucu # <-- SONUCU YANITA EKLE
        })
        os.remove(resim_yolu)  
   
    return jsonify(response_data)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=5001)
