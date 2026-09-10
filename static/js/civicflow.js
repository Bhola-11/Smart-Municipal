/**
 * CivicFlow Interactive Municipal Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Cascading Category -> SubCategory dropdown
    const categorySelect = document.getElementById('id_category');
    const subcategorySelect = document.getElementById('id_subcategory');

    if (categorySelect && subcategorySelect) {
        categorySelect.addEventListener('change', async (e) => {
            const catId = e.target.value;
            subcategorySelect.innerHTML = '<option value="">Loading subcategories...</option>';
            if (!catId) {
                subcategorySelect.innerHTML = '<option value="">Select Category First</option>';
                return;
            }
            try {
                const res = await fetch(`/complaints/api/subcategories/${catId}/`);
                const data = await res.json();
                subcategorySelect.innerHTML = '<option value="">Select Subcategory</option>';
                data.subcategories.forEach(sub => {
                    const opt = document.createElement('option');
                    opt.value = sub.id;
                    opt.textContent = sub.name;
                    subcategorySelect.appendChild(opt);
                });
            } catch (err) {
                console.error('Failed to load subcategories:', err);
                subcategorySelect.innerHTML = '<option value="">Error loading subcategories</option>';
            }
        });
    }

    // 2. Cascading Ward -> Area dropdown
    const wardSelect = document.getElementById('id_ward');
    const areaSelect = document.getElementById('id_area');

    if (wardSelect && areaSelect) {
        wardSelect.addEventListener('change', async (e) => {
            const wardId = e.target.value;
            areaSelect.innerHTML = '<option value="">Loading areas...</option>';
            if (!wardId) {
                areaSelect.innerHTML = '<option value="">Select Ward First</option>';
                return;
            }
            try {
                const res = await fetch(`/wards/api/areas/${wardId}/`);
                const data = await res.json();
                areaSelect.innerHTML = '<option value="">Select Locality / Area</option>';
                data.areas.forEach(area => {
                    const opt = document.createElement('option');
                    opt.value = area.id;
                    opt.textContent = `${area.name} (${area.postal_code})`;
                    areaSelect.appendChild(opt);
                });
            } catch (err) {
                console.error('Failed to load areas:', err);
                areaSelect.innerHTML = '<option value="">Error loading areas</option>';
            }
        });
    }

    // 3. File upload size limit validator
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file && file.size > 10 * 1024 * 1024) {
                alert('Warning: File exceeds the maximum municipal limit of 10 MB.');
                e.target.value = '';
            }
        });
    });

    // 4. Dismissible alerts
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alertBox = e.target.closest('.civic-alert');
            if (alertBox) {
                alertBox.style.display = 'none';
            }
        });
    });
});
