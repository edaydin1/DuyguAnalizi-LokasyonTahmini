import streamlit as st
import folium
from streamlit_folium import folium_static
from utils import get_video_id, get_video_transcript
from location_extractor import LocationExtractor
from text_analyzer import analyze_transcript, analyze_video_title
import time
import pandas as pd
import io
from transformers import AutoTokenizer, AutoModelForSequenceClassification


####################################################################################################################

#Duygu Analizi  için kullanılan model
tokenizer = AutoTokenizer.from_pretrained("tabularisai/multilingual-sentiment-analysis")
model = AutoModelForSequenceClassification.from_pretrained("tabularisai/multilingual-sentiment-analysis")
def analyze_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = model(**inputs)
    predictions = outputs.logits.softmax(dim=-1)
    
    
    negative = predictions[0][0].item()
    neutral = predictions[0][1].item() 
    positive = predictions[0][2].item()
    
    
    sentiments = {
        'Negatif': negative,
        'Nötr': neutral,
        'Pozitif': positive
    }
    
   
    return max(sentiments, key=sentiments.get)

####################################################################################################################

st.set_page_config(
    page_title="Seyahat Lokasyonu Tespit",
    page_icon="🗺️",
    layout="wide"
)

hide_all_style = """
    <style>
    #MainMenu {visibility: hidden;} /* Sağ üstteki menüyü gizler */
    footer {visibility: hidden;}    /* "Made with Streamlit" yazısını kaldırır */
    header {visibility: hidden;}    /* Üst başlığı kaldırır */
    </style>
"""


st.markdown(hide_all_style, unsafe_allow_html=True)

# Title and description with custom styling
st.markdown("""
    <style>
    .title {
        font-size: 50px;
        font-weight: bold;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 20px;
    }
    .description {
        font-size: 20px;
        color: #566573;é
        text-align: center;
        margin-bottom: 40px;
    }
    .stButton>button {
        background-color: #2E86C1;
        color: white;
        font-size: 18px;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #1B4F72;
    }
    .stDataFrame {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .stMarkdown {
        font-size: 18px;
        color: #566573;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
        .title {
            font-size: 28px;
            font-weight: bold;
            text-align: center;
            color: #fffdfc;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            padding: 10px;
            border-radius: 10px;
        }
    </style>
    <div class="title">📍 Youtube Videosundan Lokasyon Tespit ve Duygu Analizi 🎭</div>
    """, unsafe_allow_html=True)



st.markdown("""
    <style>
        /* Giriş kutusunun genel stilleri */
        .custom-textbox input {
            font-size: 18px !important;
            padding: 12px !important;
            border: 2px solid #ff4b4b !important;
            border-radius: 8px !important;
            background-color: #fffaf0 !important;
            color: #333 !important;
            width: 100% !important;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Placeholder stilini değiştir */
        .custom-textbox input::placeholder {
            color: #ff4b4b !important;
            font-style: italic !important;
        }
    </style>
""", unsafe_allow_html=True)

youtube_url = st.text_input(
    "YouTube Video URL'si",
    placeholder="🔗 YouTube linkini buraya yapıştırmalısın...",
    key="youtube_url",
)


if youtube_url:
    try:
            
        with st.spinner('Video işleniyor...'):
            # Get video ID and transcript
            video_id = get_video_id(youtube_url)
            transcript = get_video_transcript(video_id)
               
            
            if transcript:
                # Extract locations using Gemini API
                 # Extract locations using Gemini API
                with st.spinner('Lokasyonlar tespit ediliyor...'):
                    locations_with_sentences = analyze_transcript(transcript)

                    
                    # Analiz sonucunu al ve türünü kontrol et
                    locations_with_sentences = analyze_transcript(transcript)
                   
                    
                    # Eğer None veya boş ise boş sözlük oluştur
                    if not locations_with_sentences:
                        locations_with_sentences = {}
                    
                    # Sözlük değilse hata mesajı göster ve boş sözlük kullan
                    if not isinstance(locations_with_sentences, dict):
                        st.error("Lokasyon analizi beklenmeyen bir format döndürdü")
                        locations_with_sentences = {}

              



                    locations = list(locations_with_sentences.keys())
                   # Get video title context
                    video_title = analyze_video_title(transcript[:100])  # İlk 100 karakter

                    if locations:
                        # Initialize location extractor
                        extractor = LocationExtractor()

                        # Get coordinates with context
                        coordinates = extractor.get_coordinates(locations, main_city=video_title)

                        # Filter out locations that couldn't be found
                        found_locations = [loc for loc, coord in coordinates.items() if coord]

                        if found_locations:
                            # Create DataFrame for locations
                            locations_data = {
                                'Yer Adı': [],
                                'Enlem': [],
                                'Boylam': [],
                                'Content': [],
                                'Duygu Analizi': []
                            }
                            
                            for loc in found_locations:
                                coord = coordinates[loc]
                                text_content = locations_with_sentences.get(loc, "")
                                locations_data['Yer Adı'].append(loc)
                                locations_data['Enlem'].append(coord['lat'])
                                locations_data['Boylam'].append(coord['lon'])
                                locations_data['Content'].append(text_content)
                                locations_data['Duygu Analizi'].append(analyze_sentiment(text_content))


                            df = pd.DataFrame(locations_data)
                            # Create map centered on the main city if available
                            if video_title and video_title in coordinates:
                                center_lat = coordinates[video_title]['lat']
                                center_lon = coordinates[video_title]['lon']
                            else:
                                # Use the first found location as center
                                first_loc = found_locations[0]
                                center_lat = coordinates[first_loc]['lat']
                                center_lon = coordinates[first_loc]['lon']

                            # Harita görünümü
                            st.subheader("📍 Harita Görünümü")
                            m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

                            # Add markers only for found locations
                            for loc in found_locations:
                                coord = coordinates[loc]
                                folium.Marker(
                                    location=[coord['lat'], coord['lon']],
                                    popup=f"<b>{loc}</b><br>{coord.get('display_name', '')}",
                                    icon=folium.Icon(color='red', icon='info-sign')
                                ).add_to(m)

                            # Display map
                            folium_static(m)

                            # Display DataFrame
                            st.markdown("""
                                <style>
                                @keyframes blink {
                                    0% {opacity: 1;}
                                    50% {opacity: 0;}
                                    100% {opacity: 1;}
                                }
                                .blinking-text {
                                    font-size: 70px;
                                    font-weight: bold;
                                    color: red;
                                    animation: blink 2s infinite; /* Daha yavaş yanıp sönsün */
                                }
                                </style>
                                <p class="blinking-text">📊 Lokasyon Verileri</p>
                            """, unsafe_allow_html=True)
                            st.dataframe(df)



                         

                            st.subheader("📝 Tespit Edilen Lokasyonlar")
                            if found_locations:
                                st.markdown("**✅ Bulunan Lokasyonlar:**")
                                for loc in found_locations:
                                    matched_term = coordinates[loc].get('matched_term', '')
                                    if matched_term and matched_term != loc:
                                        st.markdown(f"- **{loc}** _(eşleşen: {matched_term})_\n  _{coordinates[loc].get('display_name', '')}_")
                                    else:
                                        st.markdown(f"- **{loc}**\n  _{coordinates[loc].get('display_name', '')}_")

                            not_found = [loc for loc in locations if loc not in found_locations]
                            if not_found:
                                st.markdown("**❌ Bulunamayan Lokasyonlar:**")
                                for loc in not_found:
                                    st.markdown(f"- {loc}")

                        
                        
                            # API anahtarını kullanınız

                            if "selected_row" not in st.session_state:
                                st.session_state.selected_row = 0  

                            # Sokak görüntüsü bölümü
                            st.subheader("🌆 Sokak Görüntüsü")

                            # Selectbox ile seçim yap (session_state doğrudan kullanılıyor)
                            selected_row = st.selectbox(
                                "Sokak Görüntüsü İçin Lokasyon Seçin:",
                                range(len(df)),
                                index=st.session_state.get("selected_row", 0),  # Son seçimi koru
                                format_func=lambda x: df.iloc[x]['Yer Adı'],
                                key="selected_row"  # Widget key ile state yönetimi sağla
                            )

                            # Seçilen lokasyonun bilgilerini al
                            lat = df.iloc[selected_row]['Enlem']
                            lon = df.iloc[selected_row]['Boylam']

                            # Google Maps sokak görünümü URL'si oluştur
                            maps_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"

                            # Harita görüntüsü için embed 
                            st.components.v1.iframe(
                                f"https://www.google.com/maps/embed/v1/streetview?key=GOOGLE_API_KEY&location={lat},{lon}", 
                                height=450
                            )
                        else:
                            st.warning("Tespit edilen lokasyonların koordinatları bulunamadı.")
                    else:
                        st.warning("Videoda herhangi bir lokasyon tespit edilemedi.")
            else:
                st.error("Video alt yazısı bulunamadı.")

    except Exception as e:
        st.error(f"Bir hata oluştu: {str(e)}")





st.markdown("""
---
📌 Not: Bu uygulama YouTube videolarının alt yazılarını kullanarak lokasyon tespiti yapar.
Özellikle turistik mekanlar ve önemli noktalar için optimize edilmiştir.
""")
