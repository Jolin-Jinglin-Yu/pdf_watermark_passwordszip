import os
import tempfile


def parse_uploaded_files(uploaded_files):
    """
    把 Streamlit 上传的 PDF 文件保存到临时路径，返回文件信息列表
    """
    files_data = []

    if not uploaded_files:
        return files_data

    for uploaded_file in uploaded_files:
        suffix = os.path.splitext(uploaded_file.name)[1].lower()

        if suffix != ".pdf":
            continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        files_data.append(
            {
                "name": uploaded_file.name,
                "path": temp_path,
                "type": "pdf",
            }
        )

    return files_data