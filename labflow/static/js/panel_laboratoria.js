// Panel Laboratoria Module - JavaScript

let wszystkieLaboratoriaPanel = [];

function escapeHtmlLaboratoria(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function pobierzFiltryLaboratoriow() {
    return {
        nazwa: (document.getElementById('filtr-lab-nazwa')?.value || '').trim().toLowerCase(),
        lokalizacja: (document.getElementById('filtr-lab-lokalizacja')?.value || '').trim().toLowerCase(),
        opis: (document.getElementById('filtr-lab-opis')?.value || '').trim().toLowerCase(),
    };
}

function renderujLaboratoria() {
    const kontener = document.getElementById('lista-laboratoriow');
    if (!kontener) return;

    const userRole = window.currentUserRole || 'uzytkownik';
    const canManage = userRole === 'admin' || userRole === 'pracownik';
    const filtry = pobierzFiltryLaboratoriow();

    const laboratoria = wszystkieLaboratoriaPanel.filter(lab => {
        const nazwa = (lab.nazwa || '').toLowerCase();
        const lokalizacja = (lab.lokalizacja || '').toLowerCase();
        const opis = (lab.opis || '').toLowerCase();
        return (!filtry.nazwa || nazwa.includes(filtry.nazwa)) &&
            (!filtry.lokalizacja || lokalizacja.includes(filtry.lokalizacja)) &&
            (!filtry.opis || opis.includes(filtry.opis));
    });

    if (!laboratoria || laboratoria.length === 0) {
        kontener.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">Brak laboratoriów</p>';
        return;
    }

    let html = '<table><tr><th>Nazwa</th><th>Lokalizacja</th><th>Opis</th>' + (canManage ? '<th>Akcje</th>' : '') + '</tr>';
    html += laboratoria.map(lab => {
        if (canManage) {
            return `<tr>
                <td>${escapeHtmlLaboratoria(lab.nazwa || '')}</td>
                <td><input class="labflow-inline-input" value="${escapeHtmlLaboratoria(lab.lokalizacja || '')}" onchange="zmienLokalizacje(${lab.id}, this.value)"></td>
                <td><input class="labflow-inline-input" value="${escapeHtmlLaboratoria(lab.opis || '')}" onchange="zmienOpis(${lab.id}, this.value)"></td>
                <td><button class="labflow-btn labflow-btn-danger labflow-btn-sm" onclick="usunLaboratorium(${lab.id})">Usuń</button></td>
            </tr>`;
        }
        return `<tr><td>${escapeHtmlLaboratoria(lab.nazwa || '')}</td><td>${escapeHtmlLaboratoria(lab.lokalizacja || '')}</td><td>${escapeHtmlLaboratoria(lab.opis || '')}</td></tr>`;
    }).join('');
    html += '</table>';
    kontener.innerHTML = html;
}

async function pobierzLaboratoria() {
    try {
        const res = await fetch('/api/laboratoria/');
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        const data = await res.json();
        wszystkieLaboratoriaPanel = Array.isArray(data) ? data : [];
        renderujLaboratoria();
    } catch (error) {
        console.error('Błąd ładowania laboratoriów:', error);
        const kontener = document.getElementById('lista-laboratoriow');
        if (kontener) {
            kontener.innerHTML = '<p style="color: red;">Błąd ładowania danych. Spróbuj odświeżyć stronę.</p>';
        }
    }
}

// Obsługa formularza dodawania laboratorium
const labForm = document.getElementById('laboratorium-form');
if (labForm) {
    labForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const nazwa = document.getElementById('nazwa-lab').value;
        const lokalizacja = document.getElementById('lokalizacja-lab').value;
        const opis = document.getElementById('opis-lab').value;
        const res = await fetch('/api/laboratoria/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ nazwa, lokalizacja, opis })
        });
        if (res.ok) {
            alert('Laboratorium dodane!');
            document.getElementById('formularz-laboratorium').style.display = 'none';
            await pobierzLaboratoria();
        } else {
            alert('Błąd dodawania laboratorium!');
        }
    });
}

async function usunLaboratorium(id) {
    if (!confirm('Na pewno usunąć laboratorium?')) return;
    const res = await fetch('/api/laboratoria/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (res.ok) {
        await pobierzLaboratoria();
    } else {
        alert('Błąd usuwania!');
    }
}

async function zmienLokalizacje(id, lokalizacja) {
    const res = await fetch('/api/laboratoria/' + id + '/', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ lokalizacja })
    });
    if (!res.ok) {
        alert('Błąd zmiany lokalizacji!');
        await pobierzLaboratoria();
    }
}

async function zmienOpis(id, opis) {
    const res = await fetch('/api/laboratoria/' + id + '/', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ opis })
    });
    if (!res.ok) {
        alert('Błąd zmiany opisu!');
        await pobierzLaboratoria();
    }
}

function podlaczFiltryLaboratoriow() {
    ['filtr-lab-nazwa', 'filtr-lab-lokalizacja', 'filtr-lab-opis'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', renderujLaboratoria);
            element.addEventListener('change', renderujLaboratoria);
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    podlaczFiltryLaboratoriow();
    await pobierzLaboratoria();
});
