// Panel Serwis Module - JavaScript

let wszystkieZgloszeniaSerwisowe = [];
let wszystkieSprzetySerwis = [];

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function formatDateTime(value) {
    if (!value) return '';
    return value.replace('T', ' ').replace(/([+-]\d{2}:\d{2}|Z)$/, '').slice(0, 19);
}

function statusKey(status) {
    const normalized = String(status || '')
        .trim()
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');

    if (normalized.includes('trakcie')) return 'w trakcie';
    if (normalized.includes('zakon') || normalized.includes('zako')) return 'zakonczone';
    if (normalized.includes('nowe')) return 'nowe';
    return normalized;
}

function pobierzFiltrySerwisu() {
    return {
        status: document.getElementById('filtr-serwis-status')?.value || '',
        sprzet: document.getElementById('filtr-serwis-sprzet')?.value || '',
    };
}

async function zaladujSprzetSerwis() {
    const res = await fetch('/api/sprzet/');
    const data = await res.json();
    wszystkieSprzetySerwis = data;

    const select = document.getElementById('sprzet-serwis');
    if (select) {
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

    const filterSelect = document.getElementById('filtr-serwis-sprzet');
    if (filterSelect) {
        const currentFilter = filterSelect.value;
        filterSelect.innerHTML = '<option value="">Wszystkie</option>';
        data.forEach(s => {
            const option = document.createElement('option');
            option.value = s.id;
            option.textContent = s.nazwa;
            filterSelect.appendChild(option);
        });
        filterSelect.value = currentFilter;
    }
}

const serwisForm = document.getElementById('serwis-form');
if (serwisForm) {
    serwisForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const sprzet = document.getElementById('sprzet-serwis').value;
        const opis = document.getElementById('opis-serwis').value;
        const data_zgloszenia = new Date().toISOString();
        const status = 'nowe';
        const res = await fetch('/api/serwis/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                sprzet: parseInt(sprzet),
                data_zgloszenia,
                opis,
                status
            })
        });
        if (res.ok) {
            alert('Zgłoszenie dodane!');
            document.getElementById('formularz-serwis').style.display = 'none';
            await pokazSerwis();
            await zaladujSprzetSerwis();
            if (typeof pokazSprzet === 'function') {
                await pokazSprzet();
            }
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
    const filtry = pobierzFiltrySerwisu();

    const zgloszenia = wszystkieZgloszeniaSerwisowe.filter(s => {
        const statusMatches = !filtry.status || statusKey(s.status) === filtry.status;
        const sprzetMatches = !filtry.sprzet || String(s.sprzet || '') === filtry.sprzet;
        return statusMatches && sprzetMatches;
    });

    if (!zgloszenia.length) {
        kontener.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">Brak zgłoszeń serwisowych</p>';
        return;
    }

    kontener.innerHTML = '<table><tr><th>Sprzęt</th><th>Data zgłoszenia</th><th>Opis</th><th>Status</th></tr>' +
        zgloszenia.map(s => {
            const statusClass = s.status === 'nowe' ? 'status-nowe' : s.status === 'w trakcie' ? 'status-wtrakcie' : 'status-zakonczone';
            const statusCell = canManage
                ? `<select class="labflow-inline-select ${statusClass}" onchange="zmienStatusSerwis(${s.id}, this.value)">${['nowe', 'w trakcie', 'zakończone'].map(opt => `<option value="${opt}"${s.status===opt?' selected':''}>${opt}</option>`).join('')}</select>`
                : `<span class="${statusClass}">${escapeHtml(s.status || '')}</span>`;

            const formattedDate = s.data_zgloszenia
                ? formatDateTime(s.data_zgloszenia)
                : '';

            return `<tr>
                <td>${escapeHtml(s.sprzet_nazwa || '')}</td>
                <td>${formattedDate}</td>
                <td>${escapeHtml(s.opis || '')}</td>
                <td>${statusCell}</td>
            </tr>`;
        }).join('') + '</table>';
}

async function pokazSerwis() {
    const res = await fetch('/api/serwis/');
    wszystkieZgloszeniaSerwisowe = await res.json();
    renderujSerwis();
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
    } else {
        await pokazSerwis();
        await zaladujSprzetSerwis();
        if (typeof pokazSprzet === 'function') {
            await pokazSprzet();
        }
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('filtr-serwis-status')?.addEventListener('change', renderujSerwis);
    document.getElementById('filtr-serwis-sprzet')?.addEventListener('change', renderujSerwis);
    await zaladujSprzetSerwis();
    await pokazSerwis();
});
