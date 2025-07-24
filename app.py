from flask import Flask, render_template, request, jsonify
from transformers import pipeline
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- YENİ ---
# SABİT KATEGORİLERİ BURADA TANIMLIYORUZ
SABIT_KATEGORILER = [
    # 1. Hotel General View (Otelin Genel Görünümü)
    "Hotel exterior day shot",          # Otelin dışarıdan gündüz çekimi
    "Hotel exterior night shot",        # Otelin dışarıdan gece çekimi
    "Aerial view of the hotel",         # Otelin havadan görünümü (drone)
    "Hotel entrance and driveway",      # Otel girişi ve yolu
    "Hotel lobby and reception area",   # Lobi ve resepsiyon alanı
    "Hotel building architecture",      # Otel binasının mimarisi
    "Hotel garden and landscape",       # Otel bahçesi ve peyzajı

    # 2. Hotel Spa & Wellness Facilities (Spa & Wellness Olanakları)
    "Spa and wellness center",          # Spa ve sağlık merkezi (Genel)
    "Massage room or therapy bed",      # Masaj odası veya terapi yatağı
    "Sauna",                            # Sauna
    "Turkish bath or Hamam",            # Türk hamamı
    "Steam room",                       # Buhar odası
    "Indoor swimming pool",             # Kapalı yüzme havuzu
    "Jacuzzi or hot tub",               # Jakuzi
    "Fitness center or gym",            # Fitness merkezi veya spor salonu
    "Spa relaxation lounge",            # Spa dinlenme alanı

    # 3. Hotel Child and Baby Facilities (Çocuk ve Bebek Olanakları)
    "Kids club or indoor playground",   # Mini kulüp veya kapalı oyun alanı
    "Outdoor children's playground",    # Dış mekan çocuk parkı
    "Children's swimming pool",         # Çocuk havuzu
    "Water park with slides",           # Su kaydıraklı aquapark
    "Baby cot or crib in a room",       # Odada bebek yatağı
    "High chairs for babies",           # Bebekler için mama sandalyesi

    # 4. Hotel Sport and Entertainment Facilities (Spor ve Eğlence Olanakları)
    "Main outdoor swimming pool",       # Ana dış mekan yüzme havuzu
    "Tennis court",                     # Tenis kortu
    "Basketball or volleyball court",   # Basketbol veya voleybol sahası
    "Beach volleyball",                 # Plaj voleybolu
    "Water sports like jet ski or parasailing", # Su sporları
    "Billiards or pool table",          # Bilardo masası
    "Bowling alley",                    # Bowling salonu
    "Amphitheater or show stage",       # Amfitiyatro veya gösteri sahnesi
    "Live music or band performance",   # Canlı müzik veya grup performansı
    "Night club or disco",              # Gece kulübü veya disko

    # 5. Hotel Food and Beverage Facilities (Yiyecek ve İçecek Alanları)
    "Restaurant interior",              # Restoran içi
    "Open buffet food display",         # Açık büfe yemek sunumu
    "A'la carte restaurant dining",     # A'la carte restoran
    "Bar or pub area",                  # Bar veya pub alanı
    "Poolside bar",                     # Havuz barı
    "Beach bar",                        # Plaj barı
    "Patisserie or cafe with cakes",    # Pastane veya kafe
    "Close-up of a food dish",          # Yakın çekim yemek tabağı
    "Cocktail or drink",                # Kokteyl veya içecek

    # 6. Hotel Room (Otel Odası)
    "Hotel room bedroom area",          # Otel odası yatak alanı
    "Hotel suite with living room",     # Oturma odalı süit
    "Hotel room bathroom",              # Otel odası banyosu
    "Hotel room balcony or terrace",    # Otel odası balkonu veya terası
    "View from the hotel room",         # Otel odasından manzara

    # 7. Hotel Meeting and Conference Facilities (Toplantı ve Konferans Olanakları)
    "Conference hall or meeting room",  # Konferans salonu veya toplantı odası
    "Ballroom for events or weddings",  # Balo salonu
    "Business center",                  # İş merkezi
    "Auditorium or theater setup",      # Oditoryum veya tiyatro düzeni
    "Coffee break station",             # Kahve molası alanı
]

print("Lokal model yükleniyor...")
LOKAL_MODEL_YOLU = "./clip-model-lokal"
try:
    classifier = pipeline(
        "zero-shot-image-classification",
        model=LOKAL_MODEL_YOLU,
        local_files_only=True,
        device="mps"
    )
except Exception:
    classifier = pipeline(
        "zero-shot-image-classification",
        model=LOKAL_MODEL_YOLU,
        local_files_only=True
    )
print("Lokal model başarıyla yüklendi.")


@app.route('/')
def index():
    # Kategorileri frontend'e göndererek sayfada görünmesini sağlıyoruz
    return render_template('index.html', categories=SABIT_KATEGORILER)


@app.route('/classify', methods=['POST'])
def classify_images():
    uploaded_files = request.files.getlist("images")
    
    # --- DEĞİŞİKLİK ---
    # Artık formdan kategori okumuyoruz, doğrudan sabit listemizi kullanıyoruz.
    # Hata kontrolünü de sadece dosya seçilip seçilmediğine göre yapıyoruz.
    if not uploaded_files:
        return jsonify({'error': 'Lütfen en az bir görsel seçin.'}), 400

    resim_yollari = []
    for file in uploaded_files:
        if file.filename != '':
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            resim_yollari.append(path)
    
    # Eğer hiçbir dosya kaydedilemediyse hata ver
    if not resim_yollari:
        return jsonify({'error': 'Geçerli bir görsel dosyası seçilmedi.'}), 400

    try:
        # --- DEĞİŞİKLİK ---
        # `candidate_labels` olarak sabit listemizi veriyoruz
        tum_sonuclar = classifier(resim_yollari, candidate_labels=SABIT_KATEGORILER)
    except Exception as e:
        for path in resim_yollari:
            os.remove(path)
        return jsonify({'error': f'Model çalıştırılırken bir hata oluştu: {str(e)}'}), 500

    response_data = []
    for resim_yolu, sonuclar in zip(resim_yollari, tum_sonuclar):
        response_data.append({
            'filename': os.path.basename(resim_yolu),
            'results': sonuclar
        })
        os.remove(resim_yolu)
    
    return jsonify(response_data)


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)