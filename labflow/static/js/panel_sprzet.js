// Panel Sprzęt Module - JavaScript

// Załaduj laboratoria do formularza sprzętu
async function zaladujLaboratoriaSprzet() {
    const res = await fetch('/api/laboratoria/');
    const data = await res.json();
    wszystkieLaboratoria = data;
    // Do formularza dodawania sprzętu
    const select = document.getElementById('laboratorium-sprzet');
    select.innerHTML = '';
    data.forEach(lab => {
        const option = document.createElement('option');
        option.value = lab.id;
        option.textContent = lab.nazwa;
        select.appendChild(option);
    });
    // Do filtra
    const labFiltr = document.getElementById('filtr-laboratorium');
    if (labFiltr) {
        const wybrane = labFiltr.value;
        labFiltr.innerHTML = '<option value="">Wszystkie</option>' + data.map(l => `<option value="${l.id}">${l.nazwa}</option>`).join('');
        labFiltr.value = wybrane;
    }
}

// Obsługa formularza dodawania sprzętu
document.getElementById('sprzet-form').addEventListener('submit', async function(e) {
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
        body: JSON.stringify({
            nazwa, kategoria, status, laboratorium
        })
    });
    if (res.ok) {
        alert('Sprzęt dodany!');
        document.getElementById('formularz-sprzet').style.display = 'none';
        pokazSprzet();
    } else {
        alert('Błąd dodawania sprzętu!');
    }
});

// Wyświetlanie listy sprzętu

// --- FILTRY SPRZĘTU ---
let wszystkieSprzety = [];
let wszystkieLaboratoria = [];
let wszystkieKategorie = [];

async function pokazSprzet() {
    const res = await fetch('/api/sprzet/');
    const data = await res.json();
    wszystkieSprzety = data;
    wszystkieKategorie = [...new Set(data.map(s => s.kategoria).filter(Boolean))];
    uzupelnijFiltrySprzet();
    renderujSprzet();
}

function uzupelnijFiltrySprzet() {
    // Kategorie
    const katSelect = document.getElementById('filtr-kategoria');
    if (katSelect) {
        const wybrana = katSelect.value;
        katSelect.innerHTML = '<option value="">Wszystkie</option>' + wszystkieKategorie.map(k => `<option value="${k}">${k}</option>`).join('');
        katSelect.value = wybrana;
    }
    // Laboratoria
    const labSelect = document.getElementById('filtr-laboratorium');
    if (labSelect && Array.isArray(wszystkieLaboratoria) && wszystkieLaboratoria.length) {
        const wybrane = labSelect.value;
        labSelect.innerHTML = '<option value="">Wszystkie</option>' + wszystkieLaboratoria.map(l => `<option value="${l.id}">${l.nazwa}</option>`).join('');
        labSelect.value = wybrane;
    }
}

function renderujSprzet() {
    const kontener = document.getElementById('lista-sprzetu');
    const userRole = window.currentUserRole || 'uzytkownik';
    // Pobierz wartości filtrów
    const filtrStatus = document.getElementById('filtr-status')?.value || '';
    const filtrLab = document.getElementById('filtr-laboratorium')?.value || '';
    const filtrKat = document.getElementById('filtr-kategoria')?.value || '';
    const filtrNazwa = document.getElementById('filtr-nazwa')?.value?.toLowerCase() || '';
    let sprzety = wszystkieSprzety;
    if (filtrStatus) sprzety = sprzety.filter(s => s.status === filtrStatus);
    if (filtrLab) sprzety = sprzety.filter(s => String(s.laboratorium) === filtrLab);
    if (filtrKat) sprzety = sprzety.filter(s => s.kategoria === filtrKat);
    if (filtrNazwa) sprzety = sprzety.filter(s => s.nazwa.toLowerCase().includes(filtrNazwa));
    kontener.innerHTML = '<table><tr><th>Nazwa</th><th>Kategoria</th><th>Status</th><th>Laboratorium</th><th>Akcje</th></tr>' +
        sprzety.map(s => {
            let statusClass = '';
            if (s.status === 'dostępny') statusClass = 'status-dostepny';
            else if (s.status === 'zarezerwowany') statusClass = 'status-zarezerwowany';
            else if (s.status === 'serwis') statusClass = 'status-serwis';
            let selectHTML = '';
            if (userRole === 'admin' || userRole === 'pracownik') {
                selectHTML = ` <select style="margin-left:8px;" onchange="zmienStatusSprzetu(${s.id}, this.value)">${['dostępny','zarezerwowany','serwis'].map(opt => `<option value="${opt}"${s.status===opt?' selected':''}>${opt}</option>`).join('')}</select>`;
            }
            return `<tr><td>${s.nazwa}</td><td>${s.kategoria}</td><td><span class="${statusClass}">${s.status}</span>${selectHTML}</td><td>${s.laboratorium}</td><td><button onclick="usunSprzet(${s.id})">Usuń</button></td></tr>`;
        }).join('') + '</table>';
}

// Usuwanie sprzętu
async function usunSprzet(id) {
    if (!confirm('Na pewno usunąć sprzęt?')) return;
    const res = await fetch('/api/sprzet/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (res.ok) {
        pokazSprzet();
    } else {
        alert('Błąd usuwania!');
    }
}

// Zmiana statusu sprzętu
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
        pokazSprzet();
    }
}

window.addEventListener('DOMContentLoaded', () => {
    zaladujLaboratoriaSprzet();
    pokazSprzet();
    // Obsługa filtrów
    ['filtr-status','filtr-laboratorium','filtr-kategoria','filtr-nazwa'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', renderujSprzet);
            el.addEventListener('change', renderujSprzet);
        }
    });
});
