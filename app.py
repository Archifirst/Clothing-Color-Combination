import colorsys
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
import streamlit as st

# --- 색상 변환 함수 ---
def hex_to_hsv(hex_str):
    hex_str = hex_str.lstrip('#')
    r, g, b = [int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s * 100, v * 100

def hsv_to_hex(h, s, v):
    h = (h % 360) / 360.0
    s = max(0.0, min(100.0, s)) / 100.0
    v = max(0.0, min(100.0, v)) / 100.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}".upper()

def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}".upper()

# --- 이미지 색상 분석 ---
def analyze_clothing_colors(image, k=3):
    img = image.convert('RGB')
    img = img.resize((150, 150))
    np_img = np.array(img)
    pixels = np_img.reshape(-1, 3)

    non_white_mask = ~((pixels[:, 0] > 240) & (pixels[:, 1] > 240) & (pixels[:, 2] > 240))
    cloth_pixels = pixels[non_white_mask] if np.sum(non_white_mask) > 100 else pixels

    avg_rgb = np.mean(cloth_pixels, axis=0)
    avg_hex = rgb_to_hex(avg_rgb[0], avg_rgb[1], avg_rgb[2])

    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
    kmeans.fit(cloth_pixels)
    counts = np.bincount(kmeans.labels_)
    ordered_centers = kmeans.cluster_centers_[np.argsort(-counts)]
    dominant_hexes = [rgb_to_hex(c[0], c[1], c[2]) for c in ordered_centers]

    return avg_hex, dominant_hexes

# --- 바지 색상 기준 신발 & 양말 추천 엔진 ---
def get_footwear_and_socks(bottom_hex):
    h, s, v = hex_to_hsv(bottom_hex)
    
    # 1. 어두운 계열 바지 (블랙, 차콜, 네이비 등)
    if v < 40:
        return {
            "socks_color": bottom_hex,
            "socks_name": "바지 동색 삭스 (다리 확장)",
            "shoes_color": "#1A1A1A",
            "shoes_name": "블랙 더비 / 첼시 / 다크 스니커즈",
            "guide": "바지-양말-신발을 어둡게 연결하면 하체가 길어 보이며 포멀·모던 룩에 최적입니다."
        }
    # 2. 아주 밝은 계열 바지 (화이트, 크림, 라이트베이지)
    elif v > 80 and s < 30:
        return {
            "socks_color": "#E5E5E5",
            "socks_name": "오프화이트 / 크림 삭스",
            "shoes_color": "#F8F9FA",
            "shoes_name": "클린 화이트 스니커즈 / 독일군",
            "guide": "밝은 팬츠 아래 검정 양말은 시선이 끊기므로 밝은 톤으로 통일해 깨끗한 인상을 줍니다."
        }
    # 3. 중간 톤 및 유색 팬츠 (카키, 올리브, 브라운, 데님 계열)
    else:
        return {
            "socks_color": "#E5E5E5",
            "socks_name": "멜란지 그레이 / 아이보리 삭스",
            "shoes_color": "#4A3525" if h < 60 or h > 300 else "#222222",
            "shoes_name": "브라운 로퍼 / 볼드 캔버스화",
            "guide": "중간 톤 팬츠에는 뉴트럴한 밝은 양말을 완충재로 두고 클래식 가죽화나 캔버스로 마무리합니다."
        }

# --- 2피스 추천 로직 ---
def get_2piece_recommendations(top_hex):
    h, s, v = hex_to_hsv(top_hex)
    raw_data = {
        "톤온톤": [
            {"name": "밝은 톤 (Light)", "bottom": hsv_to_hex(h, max(15, s - 30), min(95, v + 25))},
            {"name": "깊은 톤 (Deep)", "bottom": hsv_to_hex(h, min(90, s + 15), max(25, v - 35))},
        ],
        "유사색": [
            {"name": "유사색 A", "bottom": hsv_to_hex(h - 30, max(20, s - 10), v)},
            {"name": "유사색 B", "bottom": hsv_to_hex(h + 30, max(20, s - 10), v)},
        ],
        "보색 포인트": [
            {"name": "포인트 보색", "bottom": hsv_to_hex(h + 180, s, v)},
            {"name": "소프트 보색", "bottom": hsv_to_hex(h + 180, max(25, s * 0.5), min(85, v + 10))},
        ],
        "트라이어드": [
            {"name": "삼각 조화 1", "bottom": hsv_to_hex(h + 120, max(30, s * 0.7), v)},
            {"name": "삼각 조화 2", "bottom": hsv_to_hex(h + 240, max(30, s * 0.7), v)},
        ],
        "뉴트럴 매치": [
            {"name": "오프 화이트", "bottom": "#F8F9FA"},
            {"name": "차콜 그레이", "bottom": "#343A40"},
            {"name": "소프트 베이지", "bottom": "#D8C4B6"},
            {"name": "클래식 네이비", "bottom": "#1B2A47"},
        ]
    }
    
    # 신발/양말 정보 자동 결합
    for category in raw_data.values():
        for item in category:
            item.update(get_footwear_and_socks(item["bottom"]))
    return raw_data

# --- 3피스 추천 로직 ---
def get_3piece_recommendations(outer_hex):
    h, s, v = hex_to_hsv(outer_hex)
    raw_data = {
        "톤온톤": [
            {
                "name": "소프트 톤온톤",
                "inner": hsv_to_hex(h, max(10, s - 40), min(96, v + 25)),
                "bottom": hsv_to_hex(h, min(85, s + 10), max(20, v - 30)),
                "bg": hsv_to_hex(h, max(15, s - 30), min(92, v + 20))
            },
            {
                "name": "딥 톤온톤",
                "inner": "#FFFFFF",
                "bottom": hsv_to_hex(h, min(95, s + 15), max(18, v - 45)),
                "bg": hsv_to_hex(h, min(90, s + 15), max(25, v - 35))
            }
        ],
        "유사색": [
            {
                "name": "인접 웜톤 믹스",
                "inner": "#F8F9FA",
                "bottom": hsv_to_hex(h - 30, max(20, s - 10), v),
                "bg": hsv_to_hex(h - 30, max(20, s - 10), v)
            },
            {
                "name": "인접 쿨톤 믹스",
                "inner": "#FFFFFF",
                "bottom": hsv_to_hex(h + 30, max(20, s - 10), v),
                "bg": hsv_to_hex(h + 30, max(20, s - 10), v)
            }
        ],
        "보색 포인트": [
            {
                "name": "비비드 보색 이너",
                "inner": hsv_to_hex(h + 180, max(45, s), min(90, v + 10)),
                "bottom": "#2B2D42",
                "bg": hsv_to_hex(h + 180, s, v)
            },
            {
                "name": "소프트 보색 팬츠",
                "inner": "#F8F9FA",
                "bottom": hsv_to_hex(h + 180, max(20, s * 0.5), min(85, v + 10)),
                "bg": hsv_to_hex(h + 180, max(20, s * 0.5), min(85, v + 10))
            }
        ],
        "트라이어드": [
            {
                "name": "트라이어드 A",
                "inner": "#FFFFFF",
                "bottom": hsv_to_hex(h + 120, max(25, s * 0.7), v),
                "bg": hsv_to_hex(h + 120, max(25, s * 0.7), v)
            },
            {
                "name": "트라이어드 B",
                "inner": hsv_to_hex(h + 240, max(25, s * 0.7), v),
                "bottom": "#343A40",
                "bg": hsv_to_hex(h + 240, max(25, s * 0.7), v)
            }
        ],
        "뉴트럴 매치": [
            {"name": "오프 화이트 팬츠", "inner": "#343A40", "bottom": "#F8F9FA", "bg": "#F8F9FA"},
            {"name": "차콜 그레이 팬츠", "inner": "#FFFFFF", "bottom": "#343A40", "bg": "#343A40"},
            {"name": "소프트 베이지 팬츠", "inner": "#FFFFFF", "bottom": "#D8C4B6", "bg": "#D8C4B6"},
            {"name": "클래식 네이비 팬츠", "inner": "#FAF0CA", "bottom": "#1B2A47", "bg": "#1B2A47"}
        ]
    }
    
    for category in raw_data.values():
        for item in category:
            item.update(get_footwear_and_socks(item["bottom"]))
    return raw_data

# --- 풀셋 일러스트 렌더링 함수 (상의 + 하의 + 양말 + 신발) ---
def render_full_outfit_card(top_color, bottom_color, socks_color, shoes_color, inner_color=None, label="", shoes_desc="", socks_desc="", guide=""):
    # 3피스일 경우 오픈된 아우터 SVG, 2피스일 경우 단색 티셔츠 SVG 적용
    if inner_color:
        top_svg = (
            f'<svg width="72" height="54" viewBox="0 0 32 26" style="margin-bottom:-2px; z-index:4;">'
            f'<polygon points="12,2 20,2 22,25 10,25" fill="{inner_color}" stroke="#FFFFFF" stroke-width="0.5"/>'
            f'<path d="M12 2 L4 6 L2 15 L7 16 L8 25 L12 25 Z" fill="{top_color}" stroke="#FFFFFF" stroke-width="0.8"/>'
            f'<path d="M20 2 L28 6 L30 15 L25 16 L24 25 L20 25 Z" fill="{top_color}" stroke="#FFFFFF" stroke-width="0.8"/>'
            f'</svg>'
        )
    else:
        top_svg = (
            f'<svg width="58" height="46" viewBox="0 0 24 20" style="margin-bottom:-2px; z-index:4;">'
            f'<path d="M21.99 5.42l-4.54-2.85c-.41-.26-.85-.39-1.28-.39H15c-.45 0-.87.16-1.21.43L12 4.13 10.21 2.61C9.87 2.34 9.45 2.18 9 2.18H7.83c-.43 0-.87.13-1.28.39L2 5.42V8h3v10h14V8h3V5.42z" fill="{top_color}" stroke="#FFFFFF" stroke-width="0.8"/>'
            f'</svg>'
        )

    # 하의 + 양말(발목) + 신발(슈즈 형태) 결합 SVG
    lower_svg = (
        f'<svg width="48" height="66" viewBox="0 0 24 33" style="z-index:2;">'
        f'<!-- 팬츠 -->'
        f'<path d="M 4 0 L 20 0 L 22 19 L 14 19 L 12 7 L 10 19 L 2 19 Z" fill="{bottom_color}" stroke="#FFFFFF" stroke-width="0.7"/>'
        f'<!-- 양말 (발목 노출 부위) -->'
        f'<rect x="4.5" y="19" width="4.5" height="4" fill="{socks_color}" stroke="#FFFFFF" stroke-width="0.4"/>'
        f'<rect x="15" y="19" width="4.5" height="4" fill="{socks_color}" stroke="#FFFFFF" stroke-width="0.4"/>'
        f'<!-- 신발 (좌/우 슈즈) -->'
        f'<path d="M 2.5 23 L 9 23 L 9.5 27 L 1.5 27 Z" fill="{shoes_color}" stroke="#FFFFFF" stroke-width="0.6"/>'
        f'<path d="M 15 23 L 21.5 23 L 22.5 27 L 14.5 27 Z" fill="{shoes_color}" stroke="#FFFFFF" stroke-width="0.6"/>'
        f'</svg>'
    )

    # 파츠별 칩 생성
    if inner_color:
        chip_inner = f'<div><span style="display:inline-block; width:8px; height:8px; background:{inner_color}; border-radius:2px; border:1px solid #aaa; margin-right:2px; vertical-align:middle;"></span>이너</div>'
    else:
        chip_inner = ''
        
    chips = (
        f'<div style="display:flex; justify-content:space-around; background:#F8F9FA; padding:6px 2px; border-radius:6px; margin:6px 0 8px 0; font-size:10px; font-weight:600; color:#333;">'
        f'<div><span style="display:inline-block; width:8px; height:8px; background:{top_color}; border-radius:2px; border:1px solid #aaa; margin-right:2px; vertical-align:middle;"></span>상의</div>'
        f'{chip_inner}'
        f'<div><span style="display:inline-block; width:8px; height:8px; background:{bottom_color}; border-radius:2px; border:1px solid #aaa; margin-right:2px; vertical-align:middle;"></span>하의</div>'
        f'<div><span style="display:inline-block; width:8px; height:8px; background:{socks_color}; border-radius:2px; border:1px solid #aaa; margin-right:2px; vertical-align:middle;"></span>양말</div>'
        f'<div><span style="display:inline-block; width:8px; height:8px; background:{shoes_color}; border-radius:2px; border:1px solid #aaa; margin-right:2px; vertical-align:middle;"></span>슈즈</div>'
        f'</div>'
    )

    return (
        f'<div style="background-color:#FFFFFF; border-radius:14px; padding:16px 12px; margin:6px 0; box-shadow:0 3px 10px rgba(0,0,0,0.07); border:1px solid #EAEAEA;">'
        f'<div style="display:flex; flex-direction:column; align-items:center; margin-bottom:8px; filter:drop-shadow(0px 3px 4px rgba(0,0,0,0.15));">'
        f'{top_svg}'
        f'{lower_svg}'
        f'</div>'
        f'<div style="font-weight:700; font-size:14.5px; color:#111; text-align:center;">{label}</div>'
        f'{chips}'
        f'<div style="background:#F9FAFB; border-radius:6px; padding:8px; font-size:11.5px; line-height:1.45; color:#444; text-align:left;">'
        f'<b>👟 추천 슈즈:</b> {shoes_desc}<br>'
        f'<b>🧦 추천 양말:</b> {socks_desc}<br>'
        f'<span style="color:#777; font-size:11px; display:inline-block; margin-top:3px;">💡 {guide}</span>'
        f'</div>'
        f'</div>'
    )

def render_color_box(hex_color, label=""):
    h, s, v = hex_to_hsv(hex_color)
    text_color = "#FFFFFF" if v < 60 or s > 70 else "#111111"
    return (
        f'<div style="background-color:{hex_color}; border-radius:8px; padding:14px; text-align:center; color:{text_color}; border:1px solid rgba(0,0,0,0.1);">'
        f'<div style="font-weight:600; font-size:14px;">{label}</div>'
        f'<div style="font-size:12px;">{hex_color}</div>'
        f'</div>'
    )

# --- 메인 레이아웃 ---
st.set_page_config(page_title="의상 & 슈즈/삭스 풀코디 스타일러", layout="wide")

st.title("👔 풀셋(상의·하의·신발·양말) 컬러 매치 스타일러")

coord_mode = st.radio(
    "코디 스타일 모드를 선택하세요:",
    ("2-Piece (상의 + 하의 + 슈즈/삭스)", "3-Piece 레이어드 (아우터 + 이너 + 하의 + 슈즈/삭스)"),
    horizontal=True
)

is_3piece = "3-Piece" in coord_mode
item_title = "아우터" if is_3piece else "상의"

if "base_color" not in st.session_state:
    st.session_state.base_color = "#2B4C7E"

col1, col2 = st.columns([1, 2.3])

with col1:
    st.subheader(f"1. 기준 {item_title} 색상")
    input_tab1, input_tab2 = st.tabs(["📸 옷 사진 업로드", "🎨 팔레트 직접 선택"])
    
    with input_tab1:
        uploaded_file = st.file_uploader(f"{item_title} 사진을 올려주세요", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"업로드한 {item_title}", use_container_width=True)
            
            avg_color, dominant_colors = analyze_clothing_colors(image, k=3)
            
            st.markdown("**🏁 패턴/혼방 전체 평균톤:**")
            st.markdown(f'<div style="background:{avg_color}; height:26px; border-radius:5px; border:1px solid #aaa; margin-bottom:4px;"></div>', unsafe_allow_html=True)
            if st.button("✨ 전체 평균색 적용 (패턴/체크 추천)", use_container_width=True):
                st.session_state.base_color = avg_color
            
            st.markdown("**🎨 개별 추출 색상:**")
            cols = st.columns(3)
            for idx, c_hex in enumerate(dominant_colors):
                with cols[idx]:
                    st.markdown(f'<div style="background:{c_hex}; height:22px; border-radius:4px; border:1px solid #ccc; margin-bottom:4px;"></div>', unsafe_allow_html=True)
                    if st.button(f"색상 {idx+1}", key=f"img_col_{idx}", use_container_width=True):
                        st.session_state.base_color = c_hex

    with input_tab2:
        picked = st.color_picker("색상환에서 직접 선택", st.session_state.base_color)
        if picked != st.session_state.base_color:
            st.session_state.base_color = picked
            
        st.markdown("**자주 입는 기본 컬러:**")
        preset_cols = st.columns(4)
        presets = [("다크네이비", "#1B2A47"), ("올리브카키", "#3A4F41"), ("카멜베이지", "#A87C4F"), ("차콜그레이", "#333333")]
        for idx, (p_name, p_hex) in enumerate(presets):
            if preset_cols[idx].button(p_name):
                st.session_state.base_color = p_hex

    st.markdown("---")
    st.markdown(render_color_box(st.session_state.base_color, f"기준 {item_title} 색상"), unsafe_allow_html=True)

with col2:
    st.subheader(f"2. {coord_mode} 추천 결과")
    
    if not is_3piece:
        recs = get_2piece_recommendations(st.session_state.base_color)
        tabs = st.tabs(list(recs.keys()))
        for tab, (rule_name, outfit_list) in zip(tabs, recs.items()):
            with tab:
                r_cols = st.columns(len(outfit_list))
                for i, item in enumerate(outfit_list):
                    with r_cols[i]:
                        st.markdown(
                            render_full_outfit_card(
                                top_color=st.session_state.base_color,
                                bottom_color=item["bottom"],
                                socks_color=item["socks_color"],
                                shoes_color=item["shoes_color"],
                                label=item["name"],
                                shoes_desc=item["shoes_name"],
                                socks_desc=item["socks_name"],
                                guide=item["guide"]
                            ),
                            unsafe_allow_html=True
                        )
    else:
        recs = get_3piece_recommendations(st.session_state.base_color)
        tabs = st.tabs(list(recs.keys()))
        for tab, (rule_name, outfit_list) in zip(tabs, recs.items()):
            with tab:
                r_cols = st.columns(len(outfit_list))
                for i, item in enumerate(outfit_list):
                    with r_cols[i]:
                        st.markdown(
                            render_full_outfit_card(
                                top_color=st.session_state.base_color,
                                inner_color=item["inner"],
                                bottom_color=item["bottom"],
                                socks_color=item["socks_color"],
                                shoes_color=item["shoes_color"],
                                label=item["name"],
                                shoes_desc=item["shoes_name"],
                                socks_desc=item["socks_name"],
                                guide=item["guide"]
                            ),
                            unsafe_allow_html=True
                        )