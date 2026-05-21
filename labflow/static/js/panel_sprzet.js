// Panel Sprzęt Module - JavaScript

let wszystkieSprzety = [];
let wszystkieLaboratoria = [];
let wszystkieKategorie = [];

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

async function zaladujLaboratoriaSprzet() {
    const res = await fetch('/api/laboratoria/');
    const data = await res.json();
    wszystkieLaboratoria = data;

    const select = document.getElementById('laboratorium-sprzet');
    if (select) {
        const currentValue = select.value;
        select.innerHTML = '<option value="">Wybierz laboratorium</option>' + data.map(lab => `<option value="${lab.id}">${escapeHtml(lab.nazwa || '')}</option>`).join('');
        select.value = currentValue;
    }

    const labFiltr = document.getElementById('filtr-sprzet-laboratorium');
    if (labFiltr) {
        const wybrane = labFiltr.value;
        labFiltr.innerHTML = '<option value="">Wszystkie</option>' + data.map(l => `<option value="${l.id}">${escapeHtml(l.nazwa || '')}</option>`).join('');
        labFiltr.value = wybrane;
    }
}

const sprzetForm = document.getElementById('sprzet-form');
if (sprzetForm) {
    sprzetForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const nazwa = document.getElementById('nazwa').value;
        const kategoria = document.getElementById('kategoria').value;
        const status = document.getElementById('status').value;
        const laboratorium = document.getElementById('laboratorium-sprzet').value;
        const res = await fetch('/api/sprzet/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ nazwa, kategoria, status, laboratorium })
        });
        if (res.ok) {
            alert('Sprzęt dodany!');
            document.getElementById('formularz-sprzet').style.display = 'none';
            await pokazSprzet();
        } else {
            alert('Błąd dodawania sprzętu!');
        }
    });
}

function pobierzFiltrySprzetu() {
    return {
        status: document.getElementById('filtr-sprzet-status')?.value || '',
        laboratorium: document.getElementById('filtr-sprzet-laboratorium')?.value || '',
        kategoria: document.getElementById('filtr-sprzet-kategoria')?.value || '',
        nazwa: (document.getElementById('filtr-sprzet-nazwa')?.value || '').trim().toLowerCase(),
    };
}

async function pokazSprzet() {
    const res = await fetch('/api/sprzet/');
    const data = await res.json();
    wszystkieSprzety = data;
    wszystkieKategorie = [...new Set(data.map(s => s.kategoria).filter(Boolean))];
    uzupelnijFiltrySprzet();
    renderujSprzet();
}

function uzupelnijFiltrySprzet() {
    const katSelect = document.getElementById('filtr-sprzet-kategoria');
    if (katSelect) {
        const wybrana = katSelect.value;
        katSelect.innerHTML = '<option value="">Wszystkie</option>' + wszystkieKategorie.map(k => `<option value="${k}">${escapeHtml(k)}</option>`).join('');
        katSelect.value = wybrana;
    }

    const labSelect = document.getElementById('filtr-sprzet-laboratorium');
    if (labSelect) {
        const wybrane = labSelect.value;
        labSelect.innerHTML = '<option value="">Wszystkie</option>' + wszystkieLaboratoria.map(l => `<option value="${l.id}">${escapeHtml(l.nazwa || '')}</option>`).join('');
        labSelect.value = wybrane;
    }
}

function renderujSprzet() {
    const kontener = document.getElementById('lista-sprzetu');
    if (!kontener) return;

    const userRole = window.currentUserRole || 'uzytkownik';
    const canManage = userRole === 'admin' || userRole === 'pracownik';
    const filtry = pobierzFiltrySprzetu();

    let sprzety = wszystkieSprzety.filter(s => {
        const nazwa = (s.nazwa || '').toLowerCase();
        const kategoria = (s.kategoria || '').toLowerCase();
        const status = (s.status || '').toLowerCase();
        const laboratoriumId = String(s.laboratorium || '');
        const laboratoriumNazwa = (s.laboratorium_nazwa || '').toLowerCase();
        return (!filtry.status || status === filtry.status) &&
            (!filtry.laboratorium || laboratoriumId === filtry.laboratorium || laboratoriumNazwa.includes(filtry.laboratorium.toLowerCase())) &&
            (!filtry.kategoria || kategoria === filtry.kategoria.toLowerCase()) &&
            (!filtry.nazwa || nazwa.includes(filtry.nazwa));
    });

    let html = '<table><tr><th>Nazwa</th><th>Kategoria</th><th>Status</th><th>Laboratorium</th>' + (canManage ? '<th>Akcje</th>' : '') + '</tr>';
    html += sprzety.map(s => {
        const statusClass = s.status === 'dostępny' ? 'status-dostepny' : s.status === 'zarezerwowany' ? 'status-zarezerwowany' : 'status-serwis';
        const statusCell = canManage
            ? `<span class="${statusClass}">${escapeHtml(s.status || '')}</span> <select class="labflow-inline-select" onchange="zmienStatusSprzetu(${s.id}, this.value)">${['dostępny','zarezerwowany','serwis'].map(opt => `<option value="${opt}"${s.status===opt?' selected':''}>${opt}</option>`).join('')}</select>`
            : `<span class="${statusClass}">${escapeHtml(s.status || '')}</span>`;
        const akcjeCell = canManage
            ? `<button class="labflow-btn labflow-btn-danger labflow-btn-sm" onclick="usunSprzet(${s.id})">Usuń</button>`
            : '';
        return `<tr><td>${escapeHtml(s.nazwa || '')}</td><td>${escapeHtml(s.kategoria || '')}</td><td>${statusCell}</td><td>${escapeHtml(s.laboratorium_nazwa || '')}</td>${canManage ? `<td>${akcjeCell}</td>` : ''}</tr>`;
    }).join('');
    html += '</table>';
    kontener.innerHTML = html;
}

async function usunSprzet(id) {
    if (!confirm('Na pewno usunąć sprzęt?')) return;
    const res = await fetch('/api/sprzet/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (res.ok) {
        await pokazSprzet();
    } else {
        alert('Błąd usuwania!');
    }
}

async function zmienStatusSprzetu(id, status) {
    const res = await fetch('/api/sprzet/' + id + '/', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ status })
    });
    if (!res.ok) {
        alert('Błąd zmiany statusu!');
        await pokazSprzet();
    }
}

function podlaczFiltrySprzetu() {
    ['filtr-sprzet-status', 'filtr-sprzet-laboratorium', 'filtr-sprzet-kategoria', 'filtr-sprzet-nazwa'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', renderujSprzet);
            element.addEventListener('change', renderujSprzet);
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    podlaczFiltrySprzetu();
    await zaladujLaboratoriaSprzet();
    await pokazSprzet();
});
