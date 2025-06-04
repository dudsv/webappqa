import os
import uuid
import time
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from src.utils.text_processing import compare_texts, generate_summary, generate_summary_table
from src.utils.web_scraper import load_url_text
from src.utils.file_processing import extract_docx_text, create_excel_report

# Criar blueprint para as rotas do comparador
comparator_bp = Blueprint('comparator', __name__)

@comparator_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Processa um único par de documento DOCX e URL para comparação.
    """
    try:
        # Verificar se o arquivo foi enviado
        if 'docx_file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo DOCX enviado'}), 400
        
        docx_file = request.files['docx_file']
        web_url = request.form.get('web_url')
        
        if not docx_file or not web_url:
            return jsonify({'error': 'Arquivo DOCX e URL são obrigatórios'}), 400
        
        # Salvar arquivo temporário
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        
        docx_path = os.path.join(temp_dir, secure_filename(docx_file.filename))
        docx_file.save(docx_path)
        
        # Processar comparação
        docx_texts = extract_docx_text(docx_path)
        web_texts, main, metadata, alt_tags, title, elements = load_url_text(web_url)
        
        # Calcular similaridades
        comparison_results = compare_texts(docx_texts, web_texts)
        
        # Gerar resumo
        summary = generate_summary(comparison_results)
        summary_table = generate_summary_table(comparison_results)
        
        # Extrair avaliações veterinárias
        vet_ratings = []
        for element in elements:
            if element[0] == 'Puntuación Veterinaria':
                vet_ratings.append(element[2])
        
        # Gerar Excel
        excel_filename = f"comparison_{int(time.time())}.xlsx"
        excel_path = os.path.join(temp_dir, excel_filename)
        
        create_excel_report(
            excel_path,
            comparison_results,
            summary_table,
            elements,
            docx_path,
            web_url
        )
        
        # URL para download do Excel
        excel_url = f"/download/{os.path.basename(temp_dir)}/{excel_filename}"
        
        return jsonify({
            'success': True,
            'summary': summary,
            'summary_table': summary_table,
            'comparison': [
                {
                    'doc_text': item['doc_text'],
                    'web_text': item['web_text'],
                    'status': item['status'],
                    'similarity': item['similarity']
                }
                for item in comparison_results
            ],
            'elements': [
                {
                    'definition': elem[0],
                    'tag': elem[1],
                    'text': elem[2],
                    'link': elem[3]
                }
                for elem in elements
            ],
            'vet_ratings': vet_ratings,
            'excel_url': excel_url,
            'metadata': metadata
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@comparator_bp.route('/batch_upload', methods=['POST'])
def batch_upload():
    """
    Processa múltiplos pares de documento DOCX e URL para comparação em lote.
    Usa a mesma lógica da comparação singular para cada par.
    """
    try:
        pair_count = int(request.form.get('pair_count', 0))
        if pair_count <= 0:
            return jsonify({'error': 'Nenhum par de comparação fornecido'}), 400
        
        results = []
        
        for i in range(pair_count):
            docx_file = request.files.get(f'docx_file_{i}')
            web_url = request.form.get(f'web_url_{i}')
            
            if not docx_file or not web_url:
                continue
            
            # Salvar arquivo temporário
            temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
            os.makedirs(temp_dir, exist_ok=True)
            
            docx_path = os.path.join(temp_dir, secure_filename(docx_file.filename))
            docx_file.save(docx_path)
            
            # Processar comparação - mesma lógica da comparação singular
            docx_texts = extract_docx_text(docx_path)
            web_texts, main, metadata, alt_tags, title, elements = load_url_text(web_url)
            
            # Calcular similaridades
            comparison_results = compare_texts(docx_texts, web_texts)
            
            # Gerar resumo
            summary = generate_summary(comparison_results)
            summary_table = generate_summary_table(comparison_results)
            
            # Extrair avaliações veterinárias
            vet_ratings = []
            for element in elements:
                if element[0] == 'Puntuación Veterinaria':
                    vet_ratings.append(element[2])
            
            # Gerar Excel com formatação condicional e cores
            excel_filename = f"comparison_{i}_{int(time.time())}.xlsx"
            excel_path = os.path.join(temp_dir, excel_filename)
            
            create_excel_report(
                excel_path,
                comparison_results,
                summary_table,
                elements,
                docx_path,
                web_url
            )
            
            # URL para download do Excel
            excel_url = f"/download/{os.path.basename(temp_dir)}/{excel_filename}"
            
            # Adicionar resultado ao lote com informações detalhadas
            results.append({
                'title': f"{os.path.basename(docx_path)} e {web_url}",
                'summary': summary,
                'summary_table': summary_table,
                'comparison': [
                    {
                        'doc_text': item['doc_text'],
                        'web_text': item['web_text'],
                        'status': item['status'],
                        'similarity': item['similarity']
                    }
                    for item in comparison_results
                ],
                'elements': [
                    {
                        'definition': elem[0],
                        'tag': elem[1],
                        'text': elem[2],
                        'link': elem[3]
                    }
                    for elem in elements
                ],
                'vet_ratings': vet_ratings,
                'excel_url': excel_url,
                'metadata': metadata
            })
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@comparator_bp.route('/download/<folder>/<filename>', methods=['GET'])
def download_file(folder, filename):
    """
    Rota para download do arquivo Excel com os resultados.
    """
    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    return send_from_directory(directory, filename, as_attachment=True)
