// Panel Laboratoria Module - JavaScript

let wszystkieLaboratoriaPanel = [];
let aktualnieEdytowaneLaboratorium = null;

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

    if (!laboratoria.length) {
        kontener.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">Brak laboratoriów</p>';
        return;
    }

    let html = '<table><tr><th>Nazwa</th><th>Lokalizacja</th><th>Opis</th>' + (canManage ? '<th>Akcje</th>' : '') + '</tr>';
    html += laboratoria.map(lab => {
        const baseCells = `<td>${escapeHtmlLaboratoria(lab.nazwa || '')}</td><td>${escapeHtmlLaboratoria(lab.lokalizacja || '')}</td><td>${escapeHtmlLaboratoria(lab.opis || '')}</td>`;
        if (!canManage) return `<tr>${baseCells}</tr>`;
        return `<tr>${baseCells}<td><button class="labflow-btn labflow-btn-primary labflow-btn-sm" onclick="otworzModalLaboratorium(${lab.id})">Edytuj</button>`;
    }).join('');
    html += '</table>';
    kontener.innerHTML = html;
}

async function pobierzLaboratoria() {
    try {
        const res = await fetch('/api/laboratoria/');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
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
            labForm.reset();
            document.getElementById('formularz-laboratorium').style.display = 'none';
            await pobierzLaboratoria();
        } else {
            alert('Błąd dodawania laboratorium!');
        }
    });
}

function otworzModalLaboratorium(id) {
    const lab = wszystkieLaboratoriaPanel.find(item => Number(item.id) === Number(id));
    if (!lab) return;

    aktualnieEdytowaneLaboratorium = id;
    document.getElementById('edit-lab-id').value = id;
    document.getElementById('edit-lab-nazwa').value = lab.nazwa || '';
    document.getElementById('edit-lab-lokalizacja').value = lab.lokalizacja || '';
    document.getElementById('edit-lab-opis').value = lab.opis || '';

    const deleteButton = document.getElementById('usun-lab-modal-btn');
    if (deleteButton) {
        deleteButton.style.display = 'inline-flex';
    }

    document.getElementById('modal-overlay')?.classList.add('active');
    document.getElementById('laboratorium-modal')?.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function zamknijModalLaboratorium() {
    aktualnieEdytowaneLaboratorium = null;
    document.getElementById('laboratorium-modal')?.classList.remove('active');
    document.getElementById('modal-overlay')?.classList.remove('active');
    document.body.style.overflow = 'auto';
}

async function zapiszEdytowaneLaboratorium(e) {
    e.preventDefault();
    if (!aktualnieEdytowaneLaboratorium) return;

    const body = {
        nazwa: document.getElementById('edit-lab-nazwa').value,
        lokalizacja: document.getElementById('edit-lab-lokalizacja').value,
        opis: document.getElementById('edit-lab-opis').value
    };

    const res = await fetch('/api/laboratoria/' + aktualnieEdytowaneLaboratorium + '/', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(body)
    });

    if (res.ok) {
        zamknijModalLaboratorium();
        await pobierzLaboratoria();
        if (typeof zaladujLaboratoriaSprzet === 'function') await zaladujLaboratoriaSprzet();
        if (typeof zaladujLaboratoria === 'function') await zaladujLaboratoria();
    } else {
        alert('Błąd zapisu laboratorium!');
        await pobierzLaboratoria();
    }
}

async function usunLaboratorium(id) {
    if (!confirm('Na pewno usunąć laboratorium?')) return;
    const res = await fetch('/api/laboratoria/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (res.ok) {
        zamknijModalLaboratorium();
        await pobierzLaboratoria();
        if (typeof zaladujLaboratoriaSprzet === 'function') await zaladujLaboratoriaSprzet();
        if (typeof zaladujLaboratoria === 'function') await zaladujLaboratoria();
        if (typeof pokazSprzet === 'function') await pokazSprzet();
    } else {
        const data = await res.json().catch(() => ({}));
        alert(data.error || 'Błąd usuwania!');
    }
}

async function usunLaboratoriumZModala() {
    if (!aktualnieEdytowaneLaboratorium) return;
    await usunLaboratorium(aktualnieEdytowaneLaboratorium);
    zamknijModalLaboratorium();
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
    document.getElementById('laboratorium-edit-form')?.addEventListener('submit', zapiszEdytowaneLaboratorium);
    document.getElementById('modal-overlay')?.addEventListener('click', zamknijModalLaboratorium);
    await pobierzLaboratoria();
});
