import streamlit as st
import os
import shutil
import pandas as pd
import base64
from datetime import datetime

# 設定歸檔主資料夾與管制事項存檔路徑
TARGET_DIR = "./meeting_archive"
CSV_PATH = "./action_items.csv"

st.set_page_config(page_title="台中行道會會議記錄管理系統", layout="centered")
st.title("📂 台中行道會會議記錄管理系統")
st.write("上傳 PDF 會議記錄，系統將自動按年度、月份進行分類歸檔，並同步追蹤管制事項。")

# --- 初始化管制事項資料庫 ---
if not os.path.exists(CSV_PATH):
    df_init = pd.DataFrame(columns=["會議日期", "管制事項描述", "負責人", "辦理期限", "目前狀態"])
    df_init.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

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
            st.rerun()
        else:
            st.error("❌ 請先選擇一個 PDF 檔案再點擊上傳。")

# --- TAB 2: 會議記錄管制事項 ---
with tab2:
    st.subheader("📝 會議決議決策／管制事項追蹤")
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

    st.write("### 📊 目前管制事項清單")
    if df_items.empty:
        st.info("目前尚無任何管制事項。")
    else:
        edited_df = st.data_editor(df_items, use_container_width=True, key="data_editor")
        if st.button("💾 儲存狀態變更"):
            edited_df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
            st.success("🔄 狀態修改成功！")
            st.rerun()

# --- TAB 3: 瀏覽與下載功能（手機不彈窗終極精修版） ---
with tab3:
    st.subheader("歷年會議檔案清單")
    
    if not os.path.exists(TARGET_DIR) or not os.listdir(TARGET_DIR):
        st.info("目前尚無任何歸檔的會議記錄。")
    else:
        years = sorted(os.listdir(TARGET_DIR), reverse=True)
        selected_year = st.selectbox("選擇年份", years, key="v_year")
        
        if selected_year:
            year_path = os.path.join(TARGET_DIR, selected_year)
            months = sorted([m for m in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, m))])
            
            if not months:
                st.write("該年份內無月份資料。")
            else:
                selected_month = st.selectbox("選擇月份", months, key="v_month")
                
                if selected_month:
                    month_path = os.path.join(year_path, selected_month)
                    pdf_files = sorted([f for f in os.listdir(month_path) if f.lower().endswith('.pdf')])
                    
                    if not pdf_files:
                        st.write("📁 這個月還沒有會議記錄。")
                    else:
                        st.write(f"### 📅 {selected_year} {selected_month} 的會議清單：")
                        
                        active_preview_key = f"preview_{selected_year}_{selected_month}"
                        
                        for pdf in pdf_files:
                            file_full_path = os.path.join(month_path, pdf)
                            
                            try:
                                with open(file_full_path, "rb") as f:
                                    pdf_data = f.read()
                            except:
                                continue
                            
                            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                            with col1:
                                st.text(f"📄 {pdf}")
                            
                            with col2:
                                if st.button("👁️ 瀏覽", key=f"view_{pdf}", use_container_width=True):
                                    st.session_state[active_preview_key] = pdf
                                    st.rerun()
                                    
                            with col3:
                                st.download_button(
                                    label="📥 下載",
                                    data=pdf_data,
                                    file_name=pdf,
                                    mime="application/pdf",
                                    key=f"dl_btn_{pdf}",
                                    use_container_width=True
                                )
                                
                            with col4:
                                with st.popover("🗑️ 刪除", use_container_width=True):
                                    st.warning("確定永久刪除？")
                                    if st.button("🔥 確定", key=f"del_{pdf}", type="primary"):
                                        if os.path.exists(file_full_path):
                                            os.remove(file_full_path)
                                            if active_preview_key in st.session_state and st.session_state[active_preview_key] == pdf:
                                                del st.session_state[active_preview_key]
                                            st.success("已刪除")
                                            st.rerun()
                        
                        # --- 📄 網頁正下方直接展開區（智慧型防彈窗 Canvas 架構） ---
                        if active_preview_key in st.session_state:
                            target_pdf = st.session_state[active_preview_key]
                            target_path = os.path.join(month_path, target_pdf)
                            
                            if os.path.exists(target_path):
                                st.markdown("---")
                                st.write(f"🔍 **目前網頁內置預覽：{target_pdf}**")
                                
                                with open(target_path, "rb") as f:
                                    target_bytes = f.read()
                                
                                b64_data = base64.b64encode(target_bytes).decode('utf-8')
                                
                                # 💡 終極防跳窗黑科技：改用完全不帶 PDF 標籤特徵的 HTML5 Canvas + pdf.js 動態渲染
                                # 這對手機系統來說只是一個單純的「網頁白板」，因此絕對能騙過手機底層，乖乖在原地網頁正下方展開！
                                html_canvas_preview = f'''
                                <div style="text-align: center; background: #f0f2f6; padding: 10px; border-radius: 8px;">
                                    <canvas id="pdf-canvas" style="border: 1px solid #dcdcdc; max-width: 100%; height: auto; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);"></canvas>
                                </div>
                                <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>
                                <script>
                                    var pdfData = atob("{b64_data}");
                                    var loadingTask = pdfjsLib.getDocument({{data: pdfData}});
                                    loadingTask.promise.then(function(pdf) {{
                                        pdf.getPage(1).then(function(page) {{
                                            var scale = 1.5;
                                            var viewport = page.getViewport({{scale: scale}});
                                            var canvas = document.getElementById('pdf-canvas');
                                            var context = canvas.getContext('2d');
                                            canvas.height = viewport.height;
                                            canvas.width = viewport.width;
                                            var renderContext = {{
                                                canvasContext: context,
                                                viewport: viewport
                                            }};
                                            page.render(renderContext);
                                        }});
                                    }});
                                </script>
                                '''
                                st.components.v1.html(html_canvas_preview, height=620, scrolling=True)
                                
                                if st.button("❌ 關閉預覽", key="close_preview_btn"):
                                    del st.session_state[active_preview_key]
                                    st.rerun()
                        st.markdown("---")