// JavaScript para o Comparador de Documentos e Web

document.addEventListener('DOMContentLoaded', function() {
    // Configuração do formulário de comparação única
    const singleCompareForm = document.getElementById('singleCompareForm');
    if (singleCompareForm) {
        singleCompareForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const docxFile = document.getElementById('docxFile').files[0];
            const webUrl = document.getElementById('webUrl').value;
            
            if (!docxFile || !webUrl) {
                showError('Por favor, selecione um arquivo DOCX e insira uma URL válida.');
                return;
            }
            
            // Mostrar spinner de processamento
            document.getElementById('processingSpinner').classList.remove('d-none');
            document.getElementById('singleResults').classList.add('d-none');
            
            // Criar FormData para envio
            const formData = new FormData();
            formData.append('docx_file', docxFile);
            formData.append('web_url', webUrl);
            
            // Enviar requisição para o backend
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro ao processar a requisição');
                }
                return response.json();
            })
            .then(data => {
                // Ocultar spinner e mostrar resultados
                document.getElementById('processingSpinner').classList.add('d-none');
                document.getElementById('singleResults').classList.remove('d-none');
                
                // Atualizar contadores
                document.getElementById('exactCount').textContent = data.summary.exact;
                document.getElementById('similarCount').textContent = data.summary.similar;
                document.getElementById('partialCount').textContent = data.summary.partial;
                document.getElementById('missingCount').textContent = data.summary.missing;
                
                // Configurar link para download do Excel
                document.getElementById('downloadExcel').href = data.excel_url;
                
                // Preencher tabela de comparação
                const comparisonTableBody = document.getElementById('comparisonTableBody');
                comparisonTableBody.innerHTML = '';
                
                data.comparison.forEach(item => {
                    const row = document.createElement('tr');
                    
                    // Adicionar classe de status à linha
                    if (item.status === 'Exato') {
                        row.classList.add('status-exact');
                    } else if (item.status === 'Similar') {
                        row.classList.add('status-similar');
                    } else if (item.status === 'Parcial') {
                        row.classList.add('status-partial');
                    } else {
                        row.classList.add('status-missing');
                    }
                    
                    // Criar células
                    const docTextCell = document.createElement('td');
                    docTextCell.textContent = item.doc_text;
                    docTextCell.className = 'text-cell';
                    
                    const webTextCell = document.createElement('td');
                    webTextCell.textContent = item.web_text || 'Não encontrado';
                    webTextCell.className = 'text-cell';
                    
                    const statusCell = document.createElement('td');
                    statusCell.textContent = item.status;
                    
                    const similarityCell = document.createElement('td');
                    similarityCell.textContent = item.similarity !== null ? `${(item.similarity * 100).toFixed(2)}%` : 'N/A';
                    
                    // Adicionar células à linha
                    row.appendChild(docTextCell);
                    row.appendChild(webTextCell);
                    row.appendChild(statusCell);
                    row.appendChild(similarityCell);
                    
                    // Adicionar linha à tabela
                    comparisonTableBody.appendChild(row);
                });
                
                // Preencher tabela de resumo
                const summaryTableBody = document.getElementById('summaryTableBody');
                summaryTableBody.innerHTML = '';
                
                Object.entries(data.summary_table).forEach(([status, info]) => {
                    const row = document.createElement('tr');
                    
                    const statusCell = document.createElement('td');
                    statusCell.textContent = status;
                    
                    const countCell = document.createElement('td');
                    countCell.textContent = info.count;
                    
                    const percentCell = document.createElement('td');
                    percentCell.textContent = `${info.percent.toFixed(2)}%`;
                    
                    row.appendChild(statusCell);
                    row.appendChild(countCell);
                    row.appendChild(percentCell);
                    
                    summaryTableBody.appendChild(row);
                });
                
                // Preencher tabela de elementos
                const elementsTableBody = document.getElementById('elementsTableBody');
                elementsTableBody.innerHTML = '';
                
                data.elements.forEach(element => {
                    const row = document.createElement('tr');
                    
                    const defCell = document.createElement('td');
                    defCell.textContent = element.definition;
                    
                    const tagCell = document.createElement('td');
                    tagCell.textContent = element.tag;
                    
                    const textCell = document.createElement('td');
                    textCell.textContent = element.text;
                    textCell.className = 'elements-text';
                    
                    const linkCell = document.createElement('td');
                    if (element.link) {
                        const link = document.createElement('a');
                        link.href = element.link;
                        link.textContent = element.link;
                        link.target = '_blank';
                        linkCell.appendChild(link);
                        linkCell.className = 'url-cell';
                    } else {
                        linkCell.textContent = '';
                    }
                    
                    row.appendChild(defCell);
                    row.appendChild(tagCell);
                    row.appendChild(textCell);
                    row.appendChild(linkCell);
                    
                    elementsTableBody.appendChild(row);
                });
                
                // Exibir avaliação veterinária se disponível
                if (data.vet_ratings && data.vet_ratings.length > 0) {
                    const vetRatingContainer = document.getElementById('vetRatingContainer');
                    vetRatingContainer.classList.remove('d-none');
                    vetRatingContainer.innerHTML = '';
                    
                    const cardHeader = document.createElement('div');
                    cardHeader.className = 'card-header bg-light';
                    cardHeader.innerHTML = '<h5 class="mb-0">Avaliação Veterinária</h5>';
                    vetRatingContainer.appendChild(cardHeader);
                    
                    const cardBody = document.createElement('div');
                    cardBody.className = 'card-body';
                    
                    const table = document.createElement('table');
                    table.className = 'vet-rating-table';
                    
                    data.vet_ratings.forEach(rating => {
                        const match = rating.match(/^(.+):\s*(\d+)\/(\d+)$/);
                        if (match) {
                            const label = match[1];
                            const value = parseInt(match[2]);
                            const maxValue = parseInt(match[3]);
                            
                            const row = document.createElement('tr');
                            
                            const labelCell = document.createElement('td');
                            labelCell.textContent = label;
                            
                            const ratingCell = document.createElement('td');
                            ratingCell.className = 'vet-rating-value';
                            
                            const stars = document.createElement('div');
                            stars.className = 'rating-stars';
                            
                            const filledStars = document.createElement('span');
                            filledStars.className = `rating-${value}`;
                            filledStars.textContent = '★'.repeat(value);
                            
                            stars.appendChild(filledStars);
                            
                            const valueText = document.createElement('span');
                            valueText.textContent = ` ${value}/${maxValue}`;
                            
                            ratingCell.appendChild(stars);
                            ratingCell.appendChild(valueText);
                            
                            row.appendChild(labelCell);
                            row.appendChild(ratingCell);
                            
                            table.appendChild(row);
                        }
                    });
                    
                    cardBody.appendChild(table);
                    vetRatingContainer.appendChild(cardBody);
                }
            })
            .catch(error => {
                document.getElementById('processingSpinner').classList.add('d-none');
                showError('Erro ao processar a comparação: ' + error.message);
            });
        });
    }
    
    // Configuração do formulário de comparação em lote
    const batchCompareForm = document.getElementById('batchCompareForm');
    const batchPairsContainer = document.getElementById('batchPairsContainer');
    const batchCount = document.getElementById('batchCount');
    
    if (batchCompareForm && batchPairsContainer && batchCount) {
        // Função para criar um par de comparação
        function createBatchPair(index) {
            const pairDiv = document.createElement('div');
            pairDiv.className = 'batch-pair';
            pairDiv.dataset.index = index;
            
            const pairHeader = document.createElement('div');
            pairHeader.className = 'batch-pair-header';
            pairHeader.textContent = `Par #${index + 1}`;
            
            const fileDiv = document.createElement('div');
            fileDiv.className = 'mb-3';
            
            const fileLabel = document.createElement('label');
            fileLabel.className = 'form-label';
            fileLabel.textContent = 'Arquivo DOCX';
            
            const fileInput = document.createElement('input');
            fileInput.className = 'form-control batch-file';
            fileInput.type = 'file';
            fileInput.accept = '.docx';
            fileInput.required = true;
            
            fileDiv.appendChild(fileLabel);
            fileDiv.appendChild(fileInput);
            
            const urlDiv = document.createElement('div');
            urlDiv.className = 'mb-3';
            
            const urlLabel = document.createElement('label');
            urlLabel.className = 'form-label';
            urlLabel.textContent = 'URL da Página Web';
            
            const urlInput = document.createElement('input');
            urlInput.className = 'form-control batch-url';
            urlInput.type = 'url';
            urlInput.placeholder = 'https://www.exemplo.com';
            urlInput.required = true;
            
            urlDiv.appendChild(urlLabel);
            urlDiv.appendChild(urlInput);
            
            pairDiv.appendChild(pairHeader);
            pairDiv.appendChild(fileDiv);
            pairDiv.appendChild(urlDiv);
            
            return pairDiv;
        }
        
        // Função para atualizar os pares de comparação
        function updateBatchPairs() {
            const count = parseInt(batchCount.value) || 1;
            batchPairsContainer.innerHTML = '';
            
            for (let i = 0; i < count; i++) {
                batchPairsContainer.appendChild(createBatchPair(i));
            }
        }
        
        // Inicializar com um par
        updateBatchPairs();
        
        // Atualizar pares quando o contador mudar
        batchCount.addEventListener('change', updateBatchPairs);
        
        // Processar envio do formulário em lote
        batchCompareForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const pairs = batchPairsContainer.querySelectorAll('.batch-pair');
            const formData = new FormData();
            
            let isValid = true;
            let pairCount = 0;
            
            pairs.forEach((pair, index) => {
                const fileInput = pair.querySelector('.batch-file');
                const urlInput = pair.querySelector('.batch-url');
                
                if (fileInput.files.length > 0 && urlInput.value) {
                    formData.append(`docx_file_${index}`, fileInput.files[0]);
                    formData.append(`web_url_${index}`, urlInput.value);
                    pairCount++;
                } else {
                    isValid = false;
                }
            });
            
            if (!isValid || pairCount === 0) {
                showError('Por favor, preencha todos os campos de arquivo e URL para cada par.');
                return;
            }
            
            formData.append('pair_count', pairCount);
            
            // Mostrar spinner de processamento
            document.getElementById('batchProcessingSpinner').classList.remove('d-none');
            document.getElementById('batchResults').classList.add('d-none');
            
            // Enviar requisição para o backend
            fetch('/batch_upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro ao processar a requisição em lote');
                }
                return response.json();
            })
            .then(data => {
                // Ocultar spinner e mostrar resultados
                document.getElementById('batchProcessingSpinner').classList.add('d-none');
                document.getElementById('batchResults').classList.remove('d-none');
                
                // Preencher tabela de resultados em lote
                const batchResultsTableBody = document.getElementById('batchResultsTableBody');
                batchResultsTableBody.innerHTML = '';
                
                data.results.forEach((result, index) => {
                    const row = document.createElement('tr');
                    
                    const indexCell = document.createElement('td');
                    indexCell.textContent = index + 1;
                    
                    const titleCell = document.createElement('td');
                    titleCell.textContent = result.title || `Comparação ${index + 1}`;
                    
                    const exactCell = document.createElement('td');
                    exactCell.textContent = result.summary.exact;
                    
                    const similarCell = document.createElement('td');
                    similarCell.textContent = result.summary.similar;
                    
                    const partialCell = document.createElement('td');
                    partialCell.textContent = result.summary.partial;
                    
                    const missingCell = document.createElement('td');
                    missingCell.textContent = result.summary.missing;
                    
                    const totalCell = document.createElement('td');
                    totalCell.textContent = result.summary.total;
                    
                    const actionsCell = document.createElement('td');
                    
                    const downloadBtn = document.createElement('a');
                    downloadBtn.href = result.excel_url;
                    downloadBtn.className = 'btn btn-sm btn-success me-2';
                    downloadBtn.innerHTML = '<i class="bi bi-file-earmark-excel"></i> Excel';
                    
                    const viewBtn = document.createElement('button');
                    viewBtn.type = 'button';
                    viewBtn.className = 'btn btn-sm btn-primary';
                    viewBtn.innerHTML = '<i class="bi bi-eye"></i> Ver';
                    viewBtn.dataset.resultId = index;
                    viewBtn.addEventListener('click', function() {
                        // Implementar visualização detalhada
                        alert('Visualização detalhada não implementada');
                    });
                    
                    actionsCell.appendChild(downloadBtn);
                    actionsCell.appendChild(viewBtn);
                    
                    row.appendChild(indexCell);
                    row.appendChild(titleCell);
                    row.appendChild(exactCell);
                    row.appendChild(similarCell);
                    row.appendChild(partialCell);
                    row.appendChild(missingCell);
                    row.appendChild(totalCell);
                    row.appendChild(actionsCell);
                    
                    batchResultsTableBody.appendChild(row);
                });
            })
            .catch(error => {
                document.getElementById('batchProcessingSpinner').classList.add('d-none');
                showError('Erro ao processar a comparação em lote: ' + error.message);
            });
        });
    }
    
    // Função para exibir erros
    function showError(message) {
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        document.getElementById('errorModalBody').textContent = message;
        errorModal.show();
    }
});
