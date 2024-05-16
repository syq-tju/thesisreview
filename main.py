import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from PyPDF2 import PdfReader
import openai
import re
import time
import os
from datetime import datetime

# 从openai_api_key.txt文件中读取OpenAI API密钥
def read_api_key(file_path="openai_api_key.txt"):
    with open(file_path, 'r') as file:
        api_key = file.read().strip()
    return api_key

# 配置OpenAI API密钥
openai.api_key = read_api_key()

# 读取PDF文件内容
def read_pdf(file_path):
    content = ""
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            try:
                content += page.extract_text()
            except Exception as e:
                print(f"Error extracting text from page: {e}")
    return content

# 将长文本分块
def chunk_text(text, chunk_size=3000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# 清理文本
def clean_text(text):
    # 移除所有非 ASCII 字符
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text

# 调用OpenAI API进行总结
def summarize_text(text):
    chunks = chunk_text(text, chunk_size=3000)  # 将块大小设置为3000以避免超长问题
    summaries = []
    for i, chunk in enumerate(chunks):
        chunk = clean_text(chunk)
        print(f"Processing chunk {i+1}/{len(chunks)}")
        for attempt in range(3):  # 尝试最多三次
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "你是一个学位论文评审专家."},
                        {"role": "user", "content": f"请用200字左右总结以下段落，并给出300字左右、3-5条修改意见：\n{chunk}"}
                    ],
                    temperature=0,
                    timeout=10  # 设置超时时间
                )
                summary = response['choices'][0]['message']['content'].strip()
                summaries.append(summary)
                break  # 成功则退出重试循环
            except openai.error.APIError as e:
                print(f"Error processing chunk {i+1}, attempt {attempt+1}: {e}")
                if attempt < 2:
                    time.sleep(5)  # 等待一段时间再重试
                else:
                    print(f"Failed to process chunk {i+1} after 3 attempts.")
                    summaries.append(f"Chunk {i+1} could not be processed.")
    return "\n\n".join(summaries)

# 上传并总结PDF
def upload_and_summarize():
    global file_path
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        pdf_content = read_pdf(file_path)
        summary = summarize_text(pdf_content)
        summary_text_box.delete("1.0", tk.END)
        summary_text_box.insert(tk.END, summary)

# 保存总结为TXT文件
def save_summary():
    if file_path:
        file_name = os.path.basename(file_path)
        base_name, _ = os.path.splitext(file_name)
        summary = summary_text_box.get("1.0", tk.END).strip()
        if summary:
            now = datetime.now().strftime("%Y%m%d_%H%M")
            save_path = f"{base_name}.txt"
            if os.path.exists(save_path):
                save_path = f"{base_name}_{now}.txt"
            with open(save_path, 'w', encoding='utf-8') as file:
                file.write(summary)
            print(f"Summary saved as {save_path}")
        else:
            print("No summary to save.")

# 初始化Tkinter窗口
root = tk.Tk()
root.title("PDF上传与总结")

# 上传按钮
upload_button = tk.Button(root, text="上传PDF并总结", command=upload_and_summarize)
upload_button.pack(pady=20)

# 保存按钮
save_button = tk.Button(root, text="保存总结为TXT", command=save_summary)
save_button.pack(pady=20)

# 总结后的文本框
summary_text_box = ScrolledText(root, height=20, width=80)
summary_text_box.pack(pady=20)

root.mainloop()
