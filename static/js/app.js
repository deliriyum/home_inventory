// API Base URL
const API_BASE = '/api';

// State
let currentItems = [];
let currentItemId = null;
let uploadedImagePath = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadItems();
});

// Stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();

        document.getElementById('totalItems').textContent = stats.total_items;
        document.getElementById('inventoryValue').textContent = `$${stats.inventory_value.toFixed(2)}`;
        document.getElementById('potentialProfit').textContent = `$${stats.potential_profit.toFixed(2)}`;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Items
async function loadItems(status = 'inventory') {
    try {
        const url = status ? `${API_BASE}/items?status=${status}` : `${API_BASE}/items`;
        const response = await fetch(url);
        currentItems = await response.json();

        renderItems(currentItems);
    } catch (error) {
        console.error('Error loading items:', error);
        showError('Failed to load items');
    }
}

function renderItems(items) {
    const grid = document.getElementById('itemsGrid');

    if (items.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📦</div>
                <h3>No items found</h3>
                <p>Click "Add New Item" to get started!</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = items.map(item => `
        <div class="item-card" onclick="showItemDetail(${item.id})">
            ${item.image_path ?
                `<img src="/${item.image_path}" alt="${item.name}" class="item-image">` :
                `<div class="item-image" style="display: flex; align-items: center; justify-content: center; font-size: 4rem;">📦</div>`
            }
            <div class="item-content">
                <div class="item-header">
                    <div class="item-name">${escapeHtml(item.name)}</div>
                    ${item.category ? `<div class="item-category">${escapeHtml(item.category)}</div>` : ''}
                </div>
                ${item.description ? `<div class="item-description">${escapeHtml(item.description)}</div>` : ''}
                <div class="item-prices">
                    <div class="price">
                        <span class="price-label">Retail</span>
                        <span class="price-value">${item.retail_value ? '$' + item.retail_value.toFixed(2) : 'N/A'}</span>
                    </div>
                    <div class="price">
                        <span class="price-label">Asking</span>
                        <span class="price-value">${item.asking_price ? '$' + item.asking_price.toFixed(2) : 'N/A'}</span>
                    </div>
                </div>
                <span class="item-status status-${item.status}">${item.status}</span>
            </div>
        </div>
    `).join('');
}

function filterItems() {
    const status = document.getElementById('statusFilter').value;
    loadItems(status || null);
}

// Modal management
function showAddItemModal() {
    document.getElementById('modalTitle').textContent = 'Add New Item';
    document.getElementById('itemForm').reset();
    document.getElementById('itemId').value = '';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('analysisResult').style.display = 'none';
    document.getElementById('analyzeBtn').disabled = true;
    uploadedImagePath = null;
    currentItemId = null;

    document.getElementById('itemModal').style.display = 'block';
}

function closeItemModal() {
    document.getElementById('itemModal').style.display = 'none';
}

function closeDetailModal() {
    document.getElementById('detailModal').style.display = 'none';
}

// Image upload
async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('imagePreview');
        preview.src = e.target.result;
        preview.style.display = 'block';
    };
    reader.readAsDataURL(file);

    // Upload to server
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();
        uploadedImagePath = data.path;
        document.getElementById('imagePath').value = data.path;
        document.getElementById('analyzeBtn').disabled = false;

        showSuccess('Image uploaded! Click "Analyze with AI" to identify the item.');
    } catch (error) {
        console.error('Error uploading image:', error);
        showError('Failed to upload image');
    }
}

// AI Analysis
async function analyzeWithAI() {
    if (!uploadedImagePath) {
        showError('Please upload an image first');
        return;
    }

    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '🤖 Analyzing...';

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_path: uploadedImagePath,
                description: document.getElementById('userDescription').value
            })
        });

        if (!response.ok) throw new Error('Analysis failed');

        const analysis = await response.json();

        // Populate form with analysis results
        document.getElementById('itemName').value = analysis.item_name;
        document.getElementById('aiIdentifiedName').value = analysis.item_name;
        document.getElementById('aiConfidence').value = analysis.confidence;
        document.getElementById('category').value = analysis.category;
        document.getElementById('description').value = analysis.description;
        document.getElementById('repairAssessment').value =
            typeof analysis.repair_needs === 'string' ? analysis.repair_needs : analysis.repair_needs.join(', ');
        document.getElementById('retailValue').value = analysis.estimated_retail_value;
        document.getElementById('retailValueSource').value = analysis.value_source;

        // Show analysis result
        const resultDiv = document.getElementById('analysisResult');
        resultDiv.innerHTML = `
            <h4>✨ AI Analysis Complete</h4>
            <p><strong>Identified as:</strong> ${analysis.item_name} (${(analysis.confidence * 100).toFixed(0)}% confidence)</p>
            <p><strong>Category:</strong> ${analysis.category}</p>
            <p><strong>Estimated Value:</strong> $${analysis.estimated_retail_value}</p>
            <p><strong>Condition:</strong> ${analysis.condition_assessment}</p>
        `;
        resultDiv.style.display = 'block';

        showSuccess('AI analysis complete! Review and adjust the details below.');
    } catch (error) {
        console.error('Error analyzing item:', error);
        showError('Failed to analyze item. Please fill in details manually.');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '🤖 Analyze with AI';
    }
}

// Form submission
async function handleItemSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {};

    formData.forEach((value, key) => {
        if (value !== '') {
            // Convert numeric fields
            if (['price_paid', 'retail_value', 'asking_price', 'ai_confidence'].includes(key)) {
                data[key] = parseFloat(value);
            } else {
                data[key] = value;
            }
        }
    });

    try {
        const itemId = document.getElementById('itemId').value;
        const url = itemId ? `${API_BASE}/items/${itemId}` : `${API_BASE}/items`;
        const method = itemId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to save item');

        showSuccess(itemId ? 'Item updated successfully!' : 'Item created successfully!');
        closeItemModal();
        loadItems(document.getElementById('statusFilter').value);
        loadStats();
    } catch (error) {
        console.error('Error saving item:', error);
        showError('Failed to save item');
    }
}

// Item detail view
async function showItemDetail(itemId) {
    try {
        const response = await fetch(`${API_BASE}/items/${itemId}`);
        if (!response.ok) throw new Error('Failed to load item');

        const item = await response.json();
        renderItemDetail(item);

        document.getElementById('detailModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading item detail:', error);
        showError('Failed to load item details');
    }
}

function renderItemDetail(item) {
    const detailDiv = document.getElementById('itemDetail');

    detailDiv.innerHTML = `
        <div class="detail-grid">
            <div>
                ${item.image_path ?
                    `<img src="/${item.image_path}" alt="${item.name}" class="detail-image">` :
                    `<div style="width: 100%; height: 300px; background: var(--bg-color); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 6rem;">📦</div>`
                }
            </div>
            <div>
                <h2>${escapeHtml(item.name)}</h2>
                ${item.category ? `<p style="color: var(--text-secondary); margin-bottom: 20px;">${escapeHtml(item.category)}</p>` : ''}

                <div class="detail-section">
                    <h3>Details</h3>
                    <div class="detail-info">
                        ${item.description ? `<div class="info-row"><span class="info-label">Description:</span><span class="info-value">${escapeHtml(item.description)}</span></div>` : ''}
                        ${item.condition ? `<div class="info-row"><span class="info-label">Condition:</span><span class="info-value">${escapeHtml(item.condition)}</span></div>` : ''}
                        ${item.ai_identified_name ? `<div class="info-row"><span class="info-label">AI Identified:</span><span class="info-value">${escapeHtml(item.ai_identified_name)} (${(item.ai_confidence * 100).toFixed(0)}%)</span></div>` : ''}
                        <div class="info-row"><span class="info-label">Status:</span><span class="info-value"><span class="item-status status-${item.status}">${item.status}</span></span></div>
                    </div>
                </div>

                <div class="detail-section">
                    <h3>Pricing</h3>
                    <div class="detail-info">
                        ${item.price_paid ? `<div class="info-row"><span class="info-label">Price Paid:</span><span class="info-value">$${item.price_paid.toFixed(2)}</span></div>` : ''}
                        ${item.retail_value ? `<div class="info-row"><span class="info-label">Retail Value:</span><span class="info-value">$${item.retail_value.toFixed(2)}</span></div>` : ''}
                        ${item.asking_price ? `<div class="info-row"><span class="info-label">Asking Price:</span><span class="info-value">$${item.asking_price.toFixed(2)}</span></div>` : ''}
                        ${item.retail_value_source ? `<div class="info-row"><span class="info-label">Value Source:</span><span class="info-value">${escapeHtml(item.retail_value_source)}</span></div>` : ''}
                        ${item.price_paid && item.asking_price ? `<div class="info-row"><span class="info-label">Potential Profit:</span><span class="info-value" style="color: var(--success-color); font-weight: 600;">$${(item.asking_price - item.price_paid).toFixed(2)}</span></div>` : ''}
                    </div>
                </div>

                ${item.repair_assessment ? `
                    <div class="detail-section">
                        <h3>Repair Assessment</h3>
                        <p>${escapeHtml(item.repair_assessment)}</p>
                    </div>
                ` : ''}

                ${item.repair_items && item.repair_items.length > 0 ? `
                    <div class="detail-section">
                        <h3>Bill of Materials</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="border-bottom: 2px solid var(--border-color);">
                                    <th style="text-align: left; padding: 8px;">Part</th>
                                    <th style="text-align: right; padding: 8px;">Qty</th>
                                    <th style="text-align: right; padding: 8px;">Cost</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${item.repair_items.map(ri => `
                                    <tr style="border-bottom: 1px solid var(--border-color);">
                                        <td style="padding: 8px;">${escapeHtml(ri.part_name)}</td>
                                        <td style="text-align: right; padding: 8px;">${ri.quantity}</td>
                                        <td style="text-align: right; padding: 8px;">$${(ri.estimated_cost || 0).toFixed(2)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                ` : ''}

                ${item.repair_tutorial ? `
                    <div class="detail-section">
                        <h3>Repair Tutorial</h3>
                        <div style="background: var(--bg-color); padding: 15px; border-radius: 8px; white-space: pre-wrap;">${escapeHtml(item.repair_tutorial)}</div>
                    </div>
                ` : ''}

                <div class="action-buttons">
                    <button class="btn btn-secondary btn-small" onclick="closeDetailModal(); editItem(${item.id})">✏️ Edit</button>
                    ${!item.repair_bom ? `<button class="btn btn-secondary btn-small" onclick="generateBOM(${item.id})">🔧 Generate BOM</button>` : ''}
                    ${!item.repair_tutorial ? `<button class="btn btn-secondary btn-small" onclick="generateTutorial(${item.id})">📝 Generate Tutorial</button>` : ''}
                    <button class="btn btn-secondary btn-small" onclick="recheckPrice(${item.id})">💰 Recheck Price</button>
                    ${item.status === 'inventory' ? `<button class="btn btn-success btn-small" onclick="markAsSold(${item.id})">✅ Mark as Sold</button>` : ''}
                    <button class="btn btn-danger btn-small" onclick="deleteItem(${item.id})">🗑️ Delete</button>
                </div>
            </div>
        </div>
    `;
}

// Item actions
function editItem(itemId) {
    // TODO: Implement edit functionality
    showError('Edit functionality coming soon!');
}

async function generateBOM(itemId) {
    try {
        const response = await fetch(`${API_BASE}/generate-bom/${itemId}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to generate BOM');

        showSuccess('BOM generated successfully!');
        showItemDetail(itemId); // Refresh
    } catch (error) {
        console.error('Error generating BOM:', error);
        showError('Failed to generate BOM');
    }
}

async function generateTutorial(itemId) {
    try {
        const response = await fetch(`${API_BASE}/generate-tutorial/${itemId}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to generate tutorial');

        showSuccess('Tutorial generated successfully!');
        showItemDetail(itemId); // Refresh
    } catch (error) {
        console.error('Error generating tutorial:', error);
        showError('Failed to generate tutorial');
    }
}

async function recheckPrice(itemId) {
    try {
        const response = await fetch(`${API_BASE}/price-check/${itemId}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to check price');

        const priceInfo = await response.json();
        showSuccess(`Updated price: $${priceInfo.average_price.toFixed(2)}`);
        showItemDetail(itemId); // Refresh
        loadStats();
    } catch (error) {
        console.error('Error checking price:', error);
        showError('Failed to check price');
    }
}

async function markAsSold(itemId) {
    if (!confirm('Mark this item as sold?')) return;

    try {
        const response = await fetch(`${API_BASE}/items/${itemId}/move-to-sales`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ create_sale_record: true })
        });

        if (!response.ok) throw new Error('Failed to mark as sold');

        showSuccess('Item marked as sold!');
        closeDetailModal();
        loadItems(document.getElementById('statusFilter').value);
        loadStats();
    } catch (error) {
        console.error('Error marking as sold:', error);
        showError('Failed to mark as sold');
    }
}

async function deleteItem(itemId) {
    if (!confirm('Are you sure you want to delete this item? This cannot be undone.')) return;

    try {
        const response = await fetch(`${API_BASE}/items/${itemId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete item');

        showSuccess('Item deleted successfully!');
        closeDetailModal();
        loadItems(document.getElementById('statusFilter').value);
        loadStats();
    } catch (error) {
        console.error('Error deleting item:', error);
        showError('Failed to delete item');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showSuccess(message) {
    // Simple alert for now - could be replaced with toast notification
    alert(message);
}

function showError(message) {
    alert('Error: ' + message);
}

// Close modals when clicking outside
window.onclick = function(event) {
    const itemModal = document.getElementById('itemModal');
    const detailModal = document.getElementById('detailModal');

    if (event.target === itemModal) {
        closeItemModal();
    }
    if (event.target === detailModal) {
        closeDetailModal();
    }
}
