// Replace the addItem function
async function addItem(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const item = {
        name: formData.get('name'),
        category: formData.get('category'),
        quantity: parseInt(formData.get('quantity')),
        price: parseFloat(formData.get('price')),
        description: formData.get('description') || ''
    };

    try {
        const response = await fetch('/api/items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(item)
        });
        
        if (response.ok) {
            showNotification('Item added successfully!', 'success');
            clearForm();
            showSection('inventory');
            loadInventory(); // Refresh inventory
        }
    } catch (error) {
        showNotification('Error adding item', 'error');
    }
}

// Add function to load inventory from backend
async function loadInventory() {
    try {
        const response = await fetch('/api/items');
        inventory = await response.json();
        displayInventory();
        updateDashboard();
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}