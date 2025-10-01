from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import tempfile
import os
import shutil
import base64
import logging

# Cấu hình logging cơ bản
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

@app.route('/render', methods=['POST'])
def render_latex():
    data = request.get_json()
    if not data or 'latexCode' not in data or not data['latexCode'].strip():
        return jsonify({"success": False, "message": "Field 'latexCode' is required and must not be empty."}), 400

    latex_code = data['latexCode']
    output_format = data.get('format', 'svg')

    if output_format not in ['svg', 'png']:
        return jsonify({"success": False, "message": "Invalid format. Must be 'svg' or 'png'."}), 400
    
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
            
            app.logger.info(f"Created temp tex file at {tex_file_path}")

            # Bước 1: Chạy pdflatex
            # Cải tiến: Tăng timeout và bắt cả stdout/stderr
            pdflatex_process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, tex_file_path],
                check=True, timeout=30, # Tăng timeout lên 30 giây
                capture_output=True, text=True # Bắt output để debug
            )
            app.logger.info("pdflatex completed successfully.")

            if not os.path.exists(pdf_file_path):
                 raise FileNotFoundError(f"PDF file not created. pdflatex stdout: {pdflatex_process.stdout}")

            if output_format == 'svg':
                output_file_path = os.path.join(temp_dir, 'output.svg')
                subprocess.run(['pdftocairo', '-svg',  pdf_file_path, output_file_path], check=True, timeout=15)
                mimetype = 'image/svg+xml'
                with open(output_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else: # format == 'png'
                output_file_path = os.path.join(temp_dir, 'output.png')
                subprocess.run(['pdftocairo', '-png', '-singlefile', '-r', '300', pdf_file_path, output_file_path], check=True, timeout=15)
                mimetype = 'image/png'
                with open(output_file_path, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('utf-8')

            app.logger.info(f"Successfully generated {output_format} output.")
            return jsonify({
                "success": True,
                "data": {
                    "format": output_format,
                    "mimetype": mimetype,
                    "content": content 
                }
            })

        except subprocess.CalledProcessError as e:
            # Lỗi từ command-line, ưu tiên đọc stderr
            log_details = f"Process failed with exit code {e.returncode}.\n"
            log_details += f"Stderr: {e.stderr}\n"
            log_details += f"Stdout: {e.stdout}"
            app.logger.error(f"LaTeX compilation failed: {log_details}")
            return jsonify({
                "success": False, 
                "message": "LaTeX compilation failed.",
                "details": log_details
            }), 500
        except subprocess.TimeoutExpired as e:
            error_msg = f"Process timed out after {e.timeout} seconds."
            app.logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 500
        except Exception as e:
            app.logger.error(f"An unexpected error occurred: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)