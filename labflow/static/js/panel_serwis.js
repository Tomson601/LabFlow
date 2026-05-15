// Panel Serwis Module - JavaScript

let wszystkieZgloszeniaSerwisowe = [];

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

async function zaladujSprzetSerwis() {
    const res = await fetch('/api/sprzet/');
    const data = await res.json();
    const select = document.getElementById('sprzet-serwis');
    if (!select) return;

    const currentValue = select.value;
    select.innerHTML = '<option value="">Wybierz sprzęt</option>';
    data.forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = s.nazwa;
        select.appendChild(option);
    });
    select.value = currentValue;
}

const serwisForm = document.getElementById('serwis-form');
if (serwisForm) {
    serwisForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const sprzet = document.getElementById('sprzet-serwis').value;
        const data_zgloszenia = document.getElementById('data-zgloszenia').value;
        const opis = document.getElementById('opis-serwis').value;
        const status = document.getElementById('status-serwis').value;
        const res = await fetch('/api/serwis/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ sprzet, data_zgloszenia, opis, status })
        });
        if (res.ok) {
            alert('Zgłoszenie dodane!');
            document.getElementById('formularz-serwis').style.display = 'none';
            await pokazSerwis();
        } else {
            alert('Błąd dodawania zgłoszenia!');
        }
    });
}

function renderujSerwis() {
    const kontener = document.getElementById('lista-serwis');
    if (!kontener) return;

    const userRole = window.currentUserRole || 'uzytkownik';
    const canManage = userRole === 'admin' || userRole === 'pracownik';

    kontener.innerHTML = '<table><tr><th>Sprzęt</th><th>Data zgłoszenia</th><th>Opis</th><th>Status</th>' + (canManage ? '<th>Akcje</th>' : '') + '</tr>' +
        wszystkieZgloszeniaSerwisowe.map(s => {
            const statusClass = s.status === 'nowe' ? 'status-nowe' : s.status === 'w trakcie' ? 'status-wtrakcie' : 'status-zakonczone';
            const statusCell = canManage
                ? `<select class="labflow-inline-select ${statusClass}" onchange="zmienStatusSerwis(${s.id}, this.value)">${['nowe', 'w trakcie', 'zakończone'].map(opt => `<option value="${opt}"${s.status===opt?' selected':''}>${opt}</option>`).join('')}</select>`
                : `<span class="${statusClass}">${escapeHtml(s.status || '')}</span>`;
            const akcjeCell = canManage ? `<button class="labflow-btn labflow-btn-danger labflow-btn-sm" onclick="usunSerwis(${s.id})">Usuń</button>` : '';
            return `<tr><td>${escapeHtml(s.sprzet_nazwa || '')}</td><td>${s.data_zgloszenia ? s.data_zgloszenia.replace('T', ' ').slice(0, 16) : ''}</td><td>${escapeHtml(s.opis || '')}</td><td>${statusCell}</td>${canManage ? `<td>${akcjeCell}</td>` : ''}</tr>`;
        }).join('') + '</table>';
}

async function pokazSerwis() {
    const res = await fetch('/api/serwis/');
    wszystkieZgloszeniaSerwisowe = await res.json();
    renderujSerwis();
}

async function usunSerwis(id) {
    if (!confirm('Na pewno usunąć zgłoszenie?')) return;
    const res = await fetch('/api/serwis/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (res.ok) {
        await pokazSerwis();
    } else {
        alert('Błąd usuwania!');
    }
}

async function zmienStatusSerwis(id, status) {
    const res = await fetch('/api/serwis/' + id + '/', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ status })
    });
    if (!res.ok) {
        alert('Błąd zmiany statusu!');
        await pokazSerwis();
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await zaladujSprzetSerwis();
    await pokazSerwis();
});
