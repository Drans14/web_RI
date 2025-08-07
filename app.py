from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
from flask import render_template_string
# Import dari backend
from backend.models.preprocessing import preprocess_dataframe
from backend.models.model_bert import bertopic_analysis
from backend.models.model_match import keyword_matching

# Inisialisasi Flask dengan path ke template dan static
app = Flask(__name__,
            template_folder='frontend/templates',
            static_folder='frontend/static')

# Konfigurasi folder unggahan
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Halaman utama
@app.route('/')
def index():
    return render_template(
        'index.html', 
        plot_html="", 
        best_params={})


# Upload file
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and file.filename.lower().endswith(('.csv', '.xlsx')):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        if os.path.exists(filepath):
            return 'DUPLICATE'
        file.save(filepath)
        return 'OK'
    return 'Format salah'

# Daftar file
@app.route('/files')
def list_files():
    files = []
    for fname in os.listdir(app.config['UPLOAD_FOLDER']):
        fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        if os.path.isfile(fpath):
            files.append({
                'name': fname,
                'size': os.path.getsize(fpath),
                'status': 'success' if fname.lower().endswith(('.csv', '.xlsx')) else 'fail'
            })
    return jsonify(files)

# delete file
@app.route('/delete', methods=['POST'])
def delete_file():
    try:
        file_name = request.form.get('name')  # <- Sesuaikan dengan JS: formData.append('name', file.name)
        if not file_name:
            return "No filename provided", 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            return "OK"
        else:
            return "File not found", 404

    except Exception as e:
        return f"Error: {str(e)}", 500


# Analisis file
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        filename = request.form.get('filename')
        metode = request.form.get('metode')
        
        print(f"=== ANALYZE REQUEST ===")
        print(f"Filename: {filename}")
        print(f"Method: {metode}")
        
        if not filename:
            return jsonify({'error': 'Filename tidak ditemukan'}), 400
        if not metode:
            return jsonify({'error': 'Metode tidak ditemukan'}), 400
            
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File tidak ditemukan'}), 404

        print(f"Processing file: {filepath}")

        # Load dan preprocessing
        df = pd.read_csv(filepath)
        df = preprocess_dataframe(df)
        print(f"Data loaded: {len(df)} rows")

        # Jalankan metode analisis
        if metode == 'bertopic':
            print("Starting BERTopic analysis...")
            hasil = bertopic_analysis(df)
            
            print(f"Analysis result keys: {list(hasil.keys()) if isinstance(hasil, dict) else 'Not a dict'}")

            if 'error' in hasil:
                print(f"Analysis error: {hasil['error']}")
                return jsonify({'error': hasil['error']}), 500

            # Debug plot_html
            if 'plot_html' in hasil:
                plot_html = hasil['plot_html']
                print(f"Plot HTML length: {len(plot_html)}")
                print(f"Plot HTML preview: {plot_html[:200]}...")
                
                # Cek apakah mengandung script Plotly
                if 'Plotly.newPlot' in plot_html:
                    print("✓ Plot HTML contains Plotly.newPlot")
                else:
                    print("✗ Plot HTML missing Plotly.newPlot")
                    
                # Cek apakah ada div dengan id yang benar
                if 'class="plotly-graph-div"' in plot_html:
                    print("✓ Plot HTML contains plotly-graph-div")
                else:
                    print("✗ Plot HTML missing plotly-graph-div")
            else:
                print("✗ No plot_html in result")

            response_data = {
                "plot_html": hasil["plot_html"],
                "best_params": hasil["best_params"]
            }
            
            print("Sending response to client")
            return jsonify(response_data)

        elif metode == 'keyword':
            hasil = keyword_matching(df)
            return jsonify(hasil)

        else:
            return jsonify({'error': 'Metode tidak dikenali'}), 400

    except Exception as e:
        import traceback
        print(f"=== ERROR IN ANALYZE ===")
        print(f"Error: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=False)
