import colorsys
from PIL import Image
import streamlit as st

# ==========================================
# 1. 색상 변환 및 유틸리티 함수
# ==========================================
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

# --- 순수 파이썬 의류 색상 분석 ---
def analyze_clothing_colors(image, k=3):
    img = image.convert('RGB')
    img = img.resize((60, 60))
    raw_pixels = list(img.getdata())

    # 흰색 배경(240 초과) 제외
    valid = [p for p in raw_pixels if not (p[0] > 240 and p[1] > 240 and p[2] > 240)]
    if not valid:
        valid = raw_pixels

    total = len(valid)
    avg_r = sum(p[0] for p in valid) // total
    avg_g = sum(p[1] for p in valid) // total
    avg_b = sum(p[2] for p in valid) // total
    avg_hex = rgb_to_hex(avg_r, avg_g, avg_b)

    # 32단위 양자화
    color_counts = {}
    for r, g, b in valid:
        qr, qg, qb = (r // 32) * 32, (g // 32) * 32, (b // 32) * 32
        color_counts[(qr, qg, qb)] = color_counts.get((qr, qg, qb), 0) + 1

    sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
    dominant_hexes = [rgb_to_hex(c[0][0], c[0][1], c[0][2]) for c in sorted_colors[:k]]

    while len(dominant_hexes) < k:
        dominant_hexes.append(avg_hex)

    return avg_hex, dominant_hexes

# --- 전신 사진 상/하의 영역 샘플링 분석 함수 ---
def analyze_fullbody_outfit(image):
    img = image.convert('RGB')
    w, h = img.size

    # 1. 상의 추정 영역 (상위 20%~48%, 좌우 중앙 50%)
    top_box = (int(w * 0.25), int(h * 0.20), int(w * 0.75), int(h * 0.48))
    top_crop = img.crop(top_box).resize((40, 40))
    top_pixels = list(top_crop.getdata())
    top_valid = [p for p in top_pixels if not (p[0] > 240 and p[1] > 240 and p[2] > 240)] or top_pixels
    top_r = sum(p[0] for p in top_valid) // len(top_valid)
    top_g = sum(p[1] for p in top_valid) // len(top_valid)
    top_b = sum(p[2] for p in top_valid) // len(top_valid)
    top_hex = rgb_to_hex(top_r, top_g, top_b)

    # 2. 하의 추정 영역 (상위 52%~82%, 좌우 중앙 50%)
    bottom_box = (int(w * 0.25), int(h * 0.52), int(w * 0.75), int(h * 0.82))
    bottom_crop = img.crop(bottom_box).resize((40, 40))
    bottom_pixels = list(bottom_crop.getdata())
    bottom_valid = [p for p in bottom_pixels if not (p[0] > 240 and p[1] > 240 and p[2] > 240)] or bottom_pixels
    bot_r = sum(p[0] for p in bottom_valid) // len(bottom_valid)
    bot_g = sum(p[1] for p in bottom_valid) // len(bottom_valid)
    bot_b = sum(p[2] for p in bottom_valid) // len(bottom_valid)
    bottom_hex = rgb_to_hex(bot_r, bot_g, bot_b)

    # 3. 색상 조화 및 명도 계산
    top_h, top_s, top_v = hex_to_hsv(top_hex)
    bot_h, bot_s, bot_v = hex_to_hsv(bottom_hex)
    v_diff = abs(top_v - bot_v)
    h_diff = abs(top_h - bot_h)
    if h_diff > 180:
        h_diff = 360 - h_diff

    # 컬러 조화 진단
    if v_diff < 25 and (h_diff < 35 or top_s < 20 or bot_s < 20):
        color_eval = "🌟 톤온톤 (Tone-on-Tone) 조화"
        color_desc = "상·하의 톤이 자연스럽게 이어져 시선이 분절되지 않고 키가 커 보이는 차분한 효과를 줍니다."
    elif v_diff >= 45:
        color_eval = "⚡ 명확한 콘트라스트 (명도 대비)"
        color_desc = "상·하의 경계가 뚜렷해 단정하고 시원하며, 바디 프로포션을 경쾌하게 잡아줍니다."
    else:
        color_eval = "🌿 밸런스드 내추럴 매치"
        color_desc = "과하지 않은 적당한 톤 차이로 부담 없는 데일리 룩 실루엣을 완성합니다."

    # 분위기(Mood) 판정
    avg_v = (top_v + bot_v) / 2
    if avg_v < 38:
        mood = "🖤 모던 시크 / 미니멀 다크"
        mood_tip = "밝은 컬러의 스니커즈나 목걸이, 은은한 소재 차이로 답답함을 덜어내면 더욱 세련됩니다."
    elif avg_v > 75:
        mood = "☀️ 브라이트 캐주얼 / 클린 내추럴"
        mood_tip = "전체적으로 화사하며 깨끗한 인상을 줍니다. 가죽 악세서리나 시계로 중심을 눌러주면 균형이 좋습니다."
    else:
        mood = "☕ 클래식 댄디 / 어반 데일리"
        mood_tip = "어느 상황에나 두루 잘 어울리는 안정적인 출근·데이트 무드입니다."

    return {
        "top_hex": top_hex,
        "bottom_hex": bottom_hex,
        "color_eval": color_eval,
        "color_desc": color_desc,
        "mood": mood,
        "mood_tip": mood_tip
    }

# ==========================================
# 2. 풀코디 추천 알고리즘 및 렌더링
# ==========================================
def get_footwear_and_socks(bottom_hex):
    h, s, v = hex_to_hsv(bottom_hex)
    if v < 40:
        return {
            "socks_color": bottom_hex,
            "socks_name": "바지 동색 삭스 (다리 확장)",
            "shoes_color": "#1A1A1A",
            "shoes_name": "블랙 더비 / 첼시 / 다크 스니커즈",
            "guide": "바지-양말-신발을 어둡게 연결하면 하체가 길어 보이며 포멀·모던 룩에 최적입니다."
        }
    elif v > 80 and s < 30:
        return {
            "socks_color": "#E5E5E5",
            "socks_name": "오프화이트 / 크림 삭스",
            "shoes_color": "#F8F9FA",
            "shoes_name": "클린 화이트 스니커즈 / 독일군",
            "guide": "밝은 팬츠 아래 검정 양말은 시선이 끊기므로 밝은 톤으로 통일해 깨끗한 인상을 줍니다."
        }
    else:
        return {
            "socks_color": "#E5E5E5",
            "socks_name": "멜란지 그레이 / 아이보리 삭스",
            "shoes_color": "#4A3525" if h < 60 or h > 300 else "#222222",
            "shoes_name": "브라운 로퍼 / 볼드 캔버스화",
            "guide": "중간 톤 팬츠에는 뉴트럴한 밝은 양말을 완충재로 두고 클래식 가죽화나 캔버스로 마무리합니다."
        }

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
    for category in raw_data.values():
        for item in category:
            item.update(get_footwear_and_socks(item["bottom"]))
    return raw_data

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

def render_full_outfit_card(top_color, bottom_color, socks_color, shoes_color, inner_color=None, label="", shoes_desc="", socks_desc="", guide=""):
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

    lower_svg = (
        f'<svg width="48" height="66" viewBox="0 0 24 33" style="z-index:2;">'
        f'<path d="M 4 0 L 20 0 L 22 19 L 14 19 L 12 7 L 10 19 L 2 19 Z" fill="{bottom_color}" stroke="#FFFFFF" stroke-width="0.7"/>'
        f'<rect x="4.5" y="19" width="4.5" height="4" fill="{socks_color}" stroke="#FFFFFF" stroke-width="0.4"/>'
        f'<rect x="15" y="19" width="4.5" height="4" fill="{socks_color}" stroke="#FFFFFF" stroke-width="0.4"/>'
        f'<path d="M 2.5 23 L 9 23 L 9.5 27 L 1.5 27 Z" fill="{shoes_color}" stroke="#FFFFFF" stroke-width="0.6"/>'
        f'<path d="M 15 23 L 21.5 23 L 22.5 27 L 14.5 27 Z" fill="{shoes_color}" stroke="#FFFFFF" stroke-width="0.6"/>'
        f'</svg>'
    )

    chip_inner = f'<div><span style="display:inline-block; width:8px; height:8px; background:{inner_color}; border-radius:2px; border:1px solid #aaa; margin-right:2px; vertical-align:middle;"></span>이너</div>' if inner_color else ''
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

# ==========================================
# 3. Streamlit 메인 앱 화면 구성
# ==========================================
st.set_page_config(page_title="CCC - 의상 코디네이션 스타일러", page_icon="👔", layout="wide")

main_tab1, main_tab2 = st.tabs(["🎨 의류 컬러 매치 스타일러", "📸 전신 착장 핏·컬러 AI 진단"])

# ------------------------------------------
# TAB 1: 기존 개별 의류 컬러 매칭 (촬영 기능 추가)
# ------------------------------------------
with main_tab1:
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
        input_tab1, input_tab2, input_tab3 = st.tabs(["📁 파일 업로드", "📷 직접 촬영", "🎨 팔레트 선택"])
        
        target_img = None

        with input_tab1:
            uploaded_file = st.file_uploader(f"{item_title} 사진 업로드", type=["jpg", "jpeg", "png"], key="single_upload")
            if uploaded_file is not None:
                target_img = Image.open(uploaded_file)

        with input_tab2:
            camera_file = st.camera_input(f"{item_title} 직접 촬영", key="single_camera")
            if camera_file is not None:
                target_img = Image.open(camera_file)

        if target_img is not None:
            st.image(target_img, caption=f"분석 대상 {item_title}", use_container_width=True)
            avg_color, dominant_colors = analyze_clothing_colors(target_img, k=3)
            
            st.markdown("**🏁 패턴/혼방 전체 평균톤:**")
            st.markdown(f'<div style="background:{avg_color}; height:26px; border-radius:5px; border:1px solid #aaa; margin-bottom:4px;"></div>', unsafe_allow_html=True)
            if st.button("✨ 전체 평균색 적용 (패턴/체크 추천)", key="btn_apply_avg", use_container_width=True):
                st.session_state.base_color = avg_color
            
            st.markdown("**🎨 개별 추출 색상:**")
            cols = st.columns(3)
            for idx, c_hex in enumerate(dominant_colors):
                with cols[idx]:
                    st.markdown(f'<div style="background:{c_hex}; height:22px; border-radius:4px; border:1px solid #ccc; margin-bottom:4px;"></div>', unsafe_allow_html=True)
                    if st.button(f"색상 {idx+1}", key=f"img_col_{idx}", use_container_width=True):
                        st.session_state.base_color = c_hex

        with input_tab3:
            picked = st.color_picker("색상환에서 직접 선택", st.session_state.base_color)
            if picked != st.session_state.base_color:
                st.session_state.base_color = picked
                
            st.markdown("**자주 입는 기본 컬러:**")
            preset_cols = st.columns(4)
            presets = [("다크네이비", "#1B2A47"), ("올리브카키", "#3A4F41"), ("카멜베이지", "#A87C4F"), ("차콜그레이", "#333333")]
            for idx, (p_name, p_hex) in enumerate(presets):
                if preset_cols[idx].button(p_name, key=f"preset_{idx}"):
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

# ------------------------------------------
# TAB 2: 신규 전신 착장 평가 및 분석
# ------------------------------------------
with main_tab2:
    st.title("📸 전신 착장(OOTD) 핏 & 컬러 종합 진단")
    st.markdown("정면 전신 거울 샷 또는 서 있는 사진을 올려주시면, 상·하의 조화와 실루엣 밸런스를 진단해 드립니다.")

    b_col1, b_col2 = st.columns([1, 1.2])

    fullbody_img = None
    with b_col1:
        st.subheader("사진 등록")
        b_input_mode = st.radio("입력 방식 선택", ["📷 카메라로 즉시 촬영", "📁 앨범에서 사진 선택"], horizontal=True)

        if b_input_mode == "📷 카메라로 즉시 촬영":
            cam_data = st.camera_input("전신이 다 보이도록 서서 촬영해주세요", key="fullbody_cam")
            if cam_data:
                fullbody_img = Image.open(cam_data)
        else:
            file_data = st.file_uploader("전신 착장 사진 업로드", type=["jpg", "jpeg", "png"], key="fullbody_file")
            if file_data:
                fullbody_img = Image.open(file_data)

        if fullbody_img:
            st.image(fullbody_img, caption="분석 대상 착장 사진", use_container_width=True)

    with b_col2:
        st.subheader("진단 리포트")
        if fullbody_img:
            with st.spinner("착장의 명도 대비, 조화도, 실루엣을 분석 중입니다..."):
                report = analyze_fullbody_outfit(fullbody_img)

            st.success("✅ 착장 분석이 완료되었습니다!")

            # 1. 색상 매치 분석
            st.markdown("#### 1. 상·하의 컬러 조화")
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.markdown(f"**감지된 상의 톤 ({report['top_hex']})**")
                st.markdown(f'<div style="background:{report["top_hex"]}; height:35px; border-radius:6px; border:1px solid #ddd;"></div>', unsafe_allow_html=True)
            with c_col2:
                st.markdown(f"**감지된 하의 톤 ({report['bottom_hex']})**")
                st.markdown(f'<div style="background:{report["bottom_hex"]}; height:35px; border-radius:6px; border:1px solid #ddd;"></div>', unsafe_allow_html=True)

            st.write("")
            st.info(f"**{report['color_eval']}**\n\n{report['color_desc']}")

            # 2. 실루엣 및 핏 피드백
            st.markdown("#### 2. 실루엣 & 핏(Fit) 가이드")
            st.markdown("""
            * **상·하체 시각 비율:** 상의를 바지 안에 깔끔하게 넣입(Tuck-in)하거나 기장이 골반선에 위치할 때 다리가 가장 길어 보입니다.
            * **실루엣 강약 조절:** 
                * 상의가 오버핏이라면 하의를 테이퍼드나 슬림 스트레이트로 잡아주는 것이 안정적입니다.
                * 하의가 와이드 팬츠라면 상의는 어깨선에 맞추거나 크롭 기장을 선택해 시선 중심을 위로 올려주세요.
            """)

            # 3. 분위기 및 스타일링 제안
            st.markdown("#### 3. 착장 무드 & 스타일링 팁")
            st.markdown(f"**{report['mood']}**")
            st.caption(f"💡 보완 팁: {report['mood_tip']}")
        else:
            st.info("👈 왼쪽에서 카메라로 촬영하거나 전신 사진을 올려주시면 분석 리포트가 표시됩니다.")
