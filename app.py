import os
import re
import streamlit as st
import pyzipper
from file_manager import parse_uploaded_files
from preview_engine import render_pdf_preview
from watermark_engine import add_watermark_to_pdf

st.set_page_config(page_title="pdf水印添加", layout="wide")

st.markdown(
    """
    <style>
    .panel {
        border: 2px solid #999;
        padding: 14px;
        border-radius: 4px;
        background: white;
        margin-bottom: 12px;
    }
    .panel-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .header-box {
        border: 2px solid #666;
        padding: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "files_data" not in st.session_state:
    st.session_state.files_data = []

if "selected_file_index" not in st.session_state:
    st.session_state.selected_file_index = 0

if "selected_batch_files" not in st.session_state:
    st.session_state.selected_batch_files = []

if "last_output_path" not in st.session_state:
    st.session_state.last_output_path = None

if "last_output_name" not in st.session_state:
    st.session_state.last_output_name = None

if "last_zip_path" not in st.session_state:
    st.session_state.last_zip_path = None

if "last_zip_name" not in st.session_state:
    st.session_state.last_zip_name = None

st.markdown('<div class="header-box">pdf水印添加</div>', unsafe_allow_html=True)

left_col, middle_col, right_col = st.columns([1.1, 1.1, 1.3])

# ----------------------------
# 左侧：上传 + 文件列表
# ----------------------------
with left_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">文件上传</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "上传 PDF 文件",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        st.session_state.files_data = parse_uploaded_files(uploaded_files)
        if st.session_state.selected_file_index >= len(st.session_state.files_data):
            st.session_state.selected_file_index = 0
        st.session_state.last_output_path = None
        st.session_state.last_output_name = None
        st.session_state.last_zip_path = None
        st.session_state.last_zip_name = None

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">文件列表</div>', unsafe_allow_html=True)

    files_data = st.session_state.files_data

    if not files_data:
        st.info("暂无文件")
    else:
        file_names = [f["name"] for f in files_data]

        # 单选：用于预览
        selected_name = st.radio(
            "选择预览文件",
            options=file_names,
            index=min(st.session_state.selected_file_index, len(file_names) - 1),
            label_visibility="collapsed",
        )
        st.session_state.selected_file_index = file_names.index(selected_name)

        st.write("批量下载选择：")
        selected_batch_files = st.multiselect(
            "选择需要批量打包下载的文件",
            options=file_names,
            default=st.session_state.selected_batch_files,
            label_visibility="collapsed",
        )
        st.session_state.selected_batch_files = selected_batch_files

        st.write(f"共 {len(files_data)} 个 PDF 文件")

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# 中间：水印设置 + 输出
# ----------------------------
with middle_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">水印设置</div>', unsafe_allow_html=True)

    watermark_text = st.text_input("文字", value="仅供内部使用，请勿复制转发")
    opacity = st.slider("透明度", min_value=0.05, max_value=1.0, value=0.3, step=0.05)
    rotation = st.slider("倾斜角度", min_value=-90, max_value=90, value=-45, step=5)
    font_size = st.slider("字号", min_value=12, max_value=72, value=36, step=2)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">输出</div>', unsafe_allow_html=True)

    files_data = st.session_state.files_data
    selected_index = st.session_state.selected_file_index

    if files_data:
        current_file = files_data[selected_index]
        output_dir = "temp"
        os.makedirs(output_dir, exist_ok=True)

        # 单文件输出
        output_name = current_file["name"].replace(".pdf", "_watermarked.pdf")
        output_path = os.path.join(output_dir, output_name)

        if st.button("生成当前文件水印结果"):
            try:
                add_watermark_to_pdf(
                    input_path=current_file["path"],
                    output_path=output_path,
                    watermark_text=watermark_text,
                    opacity=opacity,
                    rotation=rotation,
                    font_size=font_size,
                )
                st.session_state.last_output_path = output_path
                st.session_state.last_output_name = output_name
                st.success(f"处理完成：{output_name}")
            except Exception as e:
                st.error(f"处理失败：{e}")

        if (
            st.session_state.last_output_path
            and os.path.exists(st.session_state.last_output_path)
        ):
            with open(st.session_state.last_output_path, "rb") as f:
                st.download_button(
                    label="下载当前文件处理结果",
                    data=f.read(),
                    file_name=st.session_state.last_output_name,
                    mime="application/pdf",
                )

        st.divider()

        # 批量 ZIP 加密输出
        zip_password = st.text_input("压缩包密码", type="password")
        zip_password_confirm = st.text_input("确认压缩包密码", type="password")
        zip_filename_input = st.text_input("压缩包文件名", value="watermarked_batch_results_encrypted")

        if st.button("批量生成加密压缩包"):
            try:
                selected_names = st.session_state.selected_batch_files

                if not selected_names:
                    st.warning("请先在左侧多选要批量下载的文件")
                elif not zip_password:
                    st.warning("请先输入压缩包密码")
                elif zip_password != zip_password_confirm:
                    st.warning("两次输入的密码不一致")
                else:
                    generated_files = []

                    for file_info in files_data:
                        if file_info["name"] in selected_names:
                            batch_output_name = file_info["name"].replace(".pdf", "_watermarked.pdf")
                            batch_output_path = os.path.join(output_dir, batch_output_name)

                            add_watermark_to_pdf(
                                input_path=file_info["path"],
                                output_path=batch_output_path,
                                watermark_text=watermark_text,
                                opacity=opacity,
                                rotation=rotation,
                                font_size=font_size,
                            )

                            if os.path.exists(batch_output_path):
                                generated_files.append(batch_output_path)

                    if not generated_files:
                        st.error("未生成任何批量处理文件")
                    else:
                        zip_base_name = zip_filename_input.strip()

                        if not zip_base_name:
                            zip_base_name = "watermarked_batch_results_encrypted"

                        # 清理 Windows / macOS 不安全字符
                        zip_base_name = re.sub(r'[\\/:*?"<>|]', "_", zip_base_name)

                        if not zip_base_name.lower().endswith(".zip"):
                            zip_name = f"{zip_base_name}.zip"
                        else:
                            zip_name = zip_base_name

                        zip_path = os.path.join(output_dir, zip_name)

                        with pyzipper.AESZipFile(
                            zip_path,
                            "w",
                            compression=pyzipper.ZIP_DEFLATED,
                            encryption=pyzipper.WZ_AES,
                        ) as zipf:
                            zipf.setpassword(zip_password.encode("utf-8"))
                            zipf.setencryption(pyzipper.WZ_AES, nbits=256)

                            for file_path in generated_files:
                                zipf.write(file_path, arcname=os.path.basename(file_path))

                        st.session_state.last_zip_path = zip_path
                        st.session_state.last_zip_name = zip_name
                        st.success(f"批量处理完成，共生成 {len(generated_files)} 个文件，并已加密压缩")
            except Exception as e:
                st.error(f"批量处理失败：{e}")

        if (
            st.session_state.last_zip_path
            and os.path.exists(st.session_state.last_zip_path)
        ):
            with open(st.session_state.last_zip_path, "rb") as f:
                st.download_button(
                    label="下载加密压缩包 ZIP",
                    data=f.read(),
                    file_name=st.session_state.last_zip_name,
                    mime="application/zip",
                )
        else:
            st.info("请先选择多个文件并生成加密压缩包")

    else:
        st.info("请先上传文件")

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# 右侧：预览
# ----------------------------
with right_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">水印效果预览</div>', unsafe_allow_html=True)

    files_data = st.session_state.files_data
    selected_index = st.session_state.selected_file_index

    if files_data:
        current_file = files_data[selected_index]
        preview_output_path = os.path.join("temp", "preview_watermarked.pdf")

        try:
            add_watermark_to_pdf(
                input_path=current_file["path"],
                output_path=preview_output_path,
                watermark_text=watermark_text,
                opacity=opacity,
                rotation=rotation,
                font_size=font_size,
            )

            preview_image = render_pdf_preview(preview_output_path)

            if preview_image is not None:
                st.image(preview_image, caption=f"{current_file['name']}（水印预览）")
            else:
                st.warning("无法预览该文件")
        except Exception as e:
            st.error(f"预览失败：{e}")
    else:
        st.info("请先上传文件并在左侧选择文件")

    st.markdown('</div>', unsafe_allow_html=True)