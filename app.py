from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import tempfile
import os
import shutil
import base64

app = Flask(__name__)
# Cho phép request từ mọi nguồn, bạn có thể giới hạn lại sau này
CORS(app) 

@app.route('/render', methods=['POST'])
def render_latex():
    data = request.get_json()
    if not data or 'latexCode' not in data or not data['latexCode'].strip():
        return jsonify({"success": False, "message": "Field 'latexCode' is required and must not be empty."}), 400

    latex_code = data['latexCode']
    # Mặc định là svg, client có thể yêu cầu png nếu muốn
    output_format = data.get('format', 'svg') 

    if output_format not in ['svg', 'png']:
        return jsonify({"success": False, "message": "Invalid format. Must be 'svg' or 'png'."}), 400
    
    # Tạo thư mục tạm thời để làm việc, sẽ tự động được xóa sau đó
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            full_tex_document = f"""
\\documentclass[tikz,border=5pt]{{standalone}}
% --- Các gói phổ biến cho Toán & Vật Lý ---
\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath, amsfonts, amssymb}}
\\usepackage{{tikz}}
\\usepackage{{tkz-tab}}
\\usepackage{{pgfplots}}
\\pgfplotsset{{compat=1.17}}
\\usetikzlibrary{{calc, intersections}}

\\begin{{document}}
{latex_code}
\\end{{document}}
            """
            
            base_name = 'input'
            tex_file_path = os.path.join(temp_dir, f'{base_name}.tex')
            pdf_file_path = os.path.join(temp_dir, f'{base_name}.pdf')

            with open(tex_file_path, 'w', encoding='utf-8') as f:
                f.write(full_tex_document)

            # Bước 1: Chạy pdflatex để biên dịch ra PDF
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, tex_file_path],
                check=True, timeout=20 # Đặt timeout 20s
            )

            if output_format == 'svg':
                output_file_path = os.path.join(temp_dir, 'output.svg')
                # Bước 2a: Chuyển PDF sang SVG
                subprocess.run(['pdftocairo', '-svg', pdf_file_path, output_file_path], check=True, timeout=15)
                mimetype = 'image/svg+xml'
                with open(output_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else: # format == 'png'
                output_file_path = os.path.join(temp_dir, 'output.png')
                # Bước 2b: Chuyển PDF sang PNG với độ phân giải cao (300 DPI)
                subprocess.run(['pdftocairo', '-png', '-singlefile', '-r', '300', pdf_file_path, output_file_path], check=True, timeout=15)
                mimetype = 'image/png'
                with open(output_file_path, 'rb') as f:
                    # Mã hóa ảnh PNG sang Base64 để nhúng vào JSON
                    content = base64.b64encode(f.read()).decode('utf-8')

            # Trả về JSON chuẩn
            return jsonify({
                "success": True,
                "data": {
                    "format": output_format,
                    "mimetype": mimetype,
                    "content": content 
                }
            })

        except subprocess.CalledProcessError as e:
            log_file_path = os.path.join(temp_dir, f'{base_name}.log')
            log_details = "Log file not found or unreadable."
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    log_details = f.read(2000) # Giới hạn log để response không quá lớn
            
            return jsonify({
                "success": False, 
                "message": "LaTeX compilation failed.",
                "details": log_details
            }), 500
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)