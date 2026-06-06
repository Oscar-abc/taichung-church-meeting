import streamlit as st
import os
import shutil
import pandas as pd
from datetime import datetime

# 設定歸檔主資料夾與管制事項存檔路徑
TARGET_DIR = "./meeting_archive"
CSV_PATH = "./action_items.csv"

st.set_page_config(page_title="會議記錄管理系統", layout="centered")
st.title("📂 台中行道會會議記錄管理系統")
st.write("上傳 PDF 會議記錄，系統將自動按年度、月份進行分類歸檔，並同步追蹤管制事項。")

# --- 初始化管制事項資料庫 ---
if not os.path.exists(CSV_PATH):
    df_init = pd.DataFrame(columns=["會議日期", "管制事項描述", "負責人", "辦理期限", "目前狀態"])
    df_init.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

# 讀取現有資料
df_items = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# --- 介面分頁 ---
tab1, tab2, tab3 = st.tabs(["📤 上傳新會議記錄", "📝 會議記錄管制事項", "🔍 瀏覽歷年記錄"])

# --- TAB 1: 上傳功能 ---
with tab1:
    st.subheader("上傳會議 PDF")
    
    meeting_date = st.date_input("請選擇會議日期", datetime.today(), key="upload_date")
    uploaded_file = st.file_uploader("請選擇要上傳的會議記錄 (PDF)", type=["pdf"])
    
    if st.button("確認上傳並自動分類"):
        if uploaded_file is not None:
            year_str = f"{meeting_date.year}年"
            month_str = f"{meeting_date.month:02d}月"
            
            dest_folder = os.path.join(TARGET_DIR, year_str, month_str)
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            
            safe_filename = f"{meeting_date.strftime('%Y-%m-%d')}_{uploaded_file.name}"
            dest_path = os.path.join(dest_folder, safe_filename)
            
            with open(dest_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            st.success(f"🎉 上傳成功！檔案已自動歸類至：{year_str} -> {month_str}")
        else:
            st.error("❌ 請先選擇一個 PDF 檔案再點擊上傳。")

# --- TAB 2: 會議記錄管制事項 ---
with tab2:
    st.subheader("📝 會議決議決策／管制事項追蹤")
    
    # --- 新增項目表單 ---
    with st.expander("➕ 新增管制事項", expanded=False):
        with st.form("add_item_form", clear_on_submit=True):
            item_meeting_date = st.date_input("會議日期", datetime.today(), key="item_m_date")
            item_desc = st.text_area("管制事項描述（決議內容）", placeholder="請輸入需要追蹤的任務內容...")
            item_owner = st.text_input("負責人／單位", placeholder="例如：張三、行政組")
            item_deadline = st.date_input("辦理期限", datetime.today(), key="item_d_date")
            item_status = st.selectbox("初始狀態", ["未開始", "進行中", "已完成"])
            
            submit_button = st.form_submit_button("新增管制項目")
            
            if submit_button:
                if item_desc.strip() == "" or item_owner.strip() == "":
                    st.error("❌ 請填寫『管制事項描述』與『負責人』！")
                else:
                    new_data = {
                        "會議日期": item_meeting_date.strftime('%Y-%m-%d'),
                        "管制事項描述": item_desc,
                        "負責人": item_owner,
                        "辦理期限": item_deadline.strftime('%Y-%m-%d'),
                        "目前狀態": item_status
                    }
                    df_items = pd.concat([df_items, pd.DataFrame([new_data])], ignore_index=True)
                    df_items.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
                    st.success("✅ 管制事項已成功新增！")
                    st.rerun()

    # --- 顯示與編輯項目 ---
    st.write("### 📊 目前管制事項清單")
    if df_items.empty:
        st.info("目前尚無任何管制事項，請點擊上方展開『新增管制事項』開始建立。")
    else:
        status_filter = st.multiselect("動態狀態篩選", ["未開始", "進行中", "已完成"], default=["未開始", "進行中", "已完成"])
        filtered_df = df_items[df_items["目前狀態"].isin(status_filter)]
        
        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "目前狀態": st.column_config.SelectboxColumn(
                    "目前狀態",
                    help="點擊可以直接修改任務狀態",
                    options=["未開始", "進行中", "已完成"],
                    required=True,
                )
            },
            disabled=["會議日期", "管制事項描述", "負責人", "辦理期限"],
            use_container_width=True,
            key="data_editor"
        )
        
        if st.button("💾 儲存狀態變更"):
            df_items.update(edited_df)
            df_items.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
            st.success("🔄 狀態修改成功，已同步儲存！")
            st.rerun()

# --- TAB 3: 瀏覽與下載功能 ---
with tab3:
    st.subheader("歷年會議檔案清單")
    
    if not os.path.exists(TARGET_DIR) or not os.listdir(TARGET_DIR):
        st.info("目前尚無任何歸檔的會議記錄。")
    else:
        years = sorted(os.listdir(TARGET_DIR), reverse=True)
        selected_year = st.selectbox("選擇年份", years)
        
        if selected_year:
            year_path = os.path.join(TARGET_DIR, selected_year)
            months = sorted([m for m in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, m))])
            
            if not months:
                st.write("該年份內無月份資料。")
            else:
                selected_month = st.selectbox("選擇月份", months)
                
                if selected_month:
                    month_path = os.path.join(year_path, selected_month)
                    pdf_files = sorted([f for f in os.listdir(month_path) if f.lower().endswith('.pdf')])
                    
                    if not pdf_files:
                        st.write("📁 這個月還沒有會議記錄。")
                    else:
                        st.write(f"### 📅 {selected_year} {selected_month} 的會議清單：")
                        st.write("點擊右側的 **Download** 按鈕即可下載或開啟檔案：")
                        
# --- 替換這段 for 迴圈（加入刪除紅鈕功能） ---
                        for pdf in pdf_files:
                            file_full_path = os.path.join(month_path, pdf)
                            
                            # 讀取檔案內容供網頁下載
                            try:
                                with open(file_full_path, "rb") as f:
                                    pdf_data = f.read()
                            except:
                                pdf_data = b""
                            
                            # 建立左右四欄：檔名(佔3份)、瀏覽(佔1份)、下載(佔1份)、刪除(佔1份)
                            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                            with col1:
                                st.text(f"📄 {pdf}")
                            
                            with col2:
                                if st.button("👁️ 瀏覽", key=f"view_{pdf}"):
                                    st.session_state[f"preview_{selected_year}_{selected_month}"] = pdf
                                    st.rerun()
                                    
                            with col3:
                                st.download_button(
                                    label="📥 下載",
                                    data=pdf_data,
                                    file_name=pdf,
                                    mime="application/pdf",
                                    key=f"dl_{pdf}"
                                )
                                
                            with col4:
                                # 使用 streamlit 的 popover 做二次確認，防止誤點直接刪除
                                with st.popover("🗑️ 刪除", help="點擊以刪除此檔案"):
                                    st.warning("確定要永久刪除此會議記錄嗎？")
                                    if st.button("🔥 確認刪除", key=f"del_conf_{pdf}", type="primary"):
                                        if os.path.exists(file_full_path):
                                            os.remove(file_full_path)
                                            st.success(f"已刪除檔案：{pdf}")
                                            
                                            # 如果剛剛正在預覽這檔案，一併清除預覽狀態
                                            p_key = f"preview_{selected_year}_{selected_month}"
                                            if p_key in st.session_state and st.session_state[p_key] == pdf:
                                                del st.session_state[p_key]
                                                
                                            st.timer = 1
                                            st.rerun()
                        
# --- 線上預覽顯示區塊（智慧手機相容版） ---
                        preview_key = f"preview_{selected_year}_{selected_month}"
                        if preview_key in st.session_state:
                            target_pdf = st.session_state[preview_key]
                            target_path = os.path.join(month_path, target_pdf)
                            
                            if os.path.exists(target_path):
                                st.markdown("---")
                                st.write(f"🔍 **正在線上預覽：{target_pdf}**")
                                
                                # 使用 streamlit 內建功能偵測使用者是否用手機 (或寬度較小的裝置)
                                # 提示使用者手機瀏覽器的限制
                                st.info("💡 溫馨提示：若您使用【手機/平板】瀏覽，因手機系統限制，網頁內嵌預覽僅能觀看第 1 頁。請直接點擊上方檔案旁邊的 **[📥 下載]** 按鈕，即可在手機上流暢閱讀完整多頁內容！")
                                
                                import base64
                                with open(target_path, "rb") as f:
                                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                
                                pdf_display = f'''
                                <object data="data:application/pdf;base64,{base64_pdf}" type="application/pdf" width="100%" height="700px">
                                    <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700px" style="border:none;">
                                        <p>您的瀏覽器不支援線上預覽，請直接點擊右側的 [下載] 按鈕觀看。</p>
                                    </iframe>
                                </object>
                                '''
                                st.markdown(pdf_display, unsafe_allow_html=True)
                                
                                if st.button("❌ 關閉預覽"):
                                    del st.session_state[preview_key]
                                    st.rerun()
                        st.markdown("---")