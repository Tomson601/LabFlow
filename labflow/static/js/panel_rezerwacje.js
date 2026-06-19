// Panel Rezerwacje Module - JavaScript

let wszystkieLaboratoriaRezerwacje = [];
let wszystkieSprzetyRezerwacje = [];
let wszystkieRezerwacje = [];
let serwisowaneSprzetyWTrakcie = new Set();
let aktualnieEdyowanaRezerwacja = null;

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
    return value.replace('T', ' ').replace(/([+-]\d{2}:\d{2}|Z)$/, '').slice(0, 16);
}

function toLocalInputValue(value) {
    if (!value) return '';
    return value.replace('T', ' ').replace(/([+-]\d{2}:\d{2}|Z)$/, '').slice(0, 16).replace(' ', 'T');
}

function parseDateTime(value) {
    if (!value) return null;
    return new Date(String(value).replace(' ', 'T'));
}

function zakresNachodzi(startA, endA, startB, endB) {
    return startA && endA && startB && endB && startA < endB && endA > startB;
}

function pobierzPolaDostepnosci(prefix = '') {
    return {
        sprzet: document.getElementById(prefix ? `${prefix}-sprzet` : 'sprzet'),
        start: document.getElementById(prefix ? `${prefix}-data-rozpoczecia` : 'data_rozpoczecia'),
        end: document.getElementById(prefix ? `${prefix}-data-zakonczenia` : 'data_zakonczenia'),
        panel: document.getElementById(prefix ? `${prefix}-dostepnosc-sprzetu` : 'dostepnosc-sprzetu'),
    };
}

async function pokazDostepnoscSprzetu(prefix = '') {
    const pola = pobierzPolaDostepnosci(prefix);
    if (!pola.panel || !pola.sprzet) return;

    const sprzetId = pola.sprzet.value;
    pola.start?.classList.remove('availability-conflict-field');
    pola.end?.classList.remove('availability-conflict-field');

    if (!sprzetId) {
        pola.panel.innerHTML = '<div class="availability-empty">Wybierz sprzet, aby zobaczyc zajete terminy.</div>';
        return;
    }

    const params = new URLSearchParams({ sprzet: sprzetId });
    if (prefix === 'edit' && aktualnieEdyowanaRezerwacja) {
        params.set('exclude', aktualnieEdyowanaRezerwacja);
    }

    const res = await fetch('/api/rezerwacje/dostepnosc/?' + params.toString());
    if (!res.ok) {
        pola.panel.innerHTML = '<div class="availability-error">Nie udalo sie pobrac dostepnosci.</div>';
        return;
    }

    const rezerwacje = await res.json();
    const wybranyStart = parseDateTime(pola.start?.value);
    const wybranyKoniec = parseDateTime(pola.end?.value);
    const maKonflikt = rezerwacje.some(r => zakresNachodzi(
        wybranyStart,
        wybranyKoniec,
        parseDateTime(r.data_rozpoczecia),
        parseDateTime(r.data_zakonczenia)
    ));

    if (maKonflikt) {
        pola.start?.classList.add('availability-conflict-field');
        pola.end?.classList.add('availability-conflict-field');
    }

    const listaTerminow = rezerwacje.length
        ? `<ul>${rezerwacje.map(r => `<li><span>${formatDateTime(r.data_rozpoczecia)}</span><span>${formatDateTime(r.data_zakonczenia)}</span><small>${escapeHtml(r.status || '')}</small></li>`).join('')}</ul>`
        : '<div class="availability-empty">Ten sprzet nie ma aktywnych rezerwacji.</div>';

    pola.panel.innerHTML = `
        <div class="availability-title">Zajete terminy wybranego sprzetu</div>
        ${maKonflikt ? '<div class="availability-warning">Wybrany zakres nachodzi na istniejaca rezerwacje.</div>' : ''}
        ${listaTerminow}
    `;
}

function statusKey(status) {
    const normalized = String(status || '')
        .trim()
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');

    if (normalized.includes('aktywna')) return 'aktywna';
    if (normalized.includes('odrzucona')) return 'odrzucona';
    if (normalized.includes('anulowana')) return 'anulowana';
    if (normalized.includes('oczekuj')) return 'oczekujaca';
    if (normalized.includes('zako')) return 'zakonczona';
    return normalized;
}

function odswiezKalendarzJesliDostepny() {
    if (window.calendarInstance && typeof window.calendarInstance.refetchEvents === 'function') {
        window.calendarInstance.refetchEvents();
    }
}

function pobierzFiltryRezerwacji() {
    return {
        status: document.getElementById('filtr-rezerwacje-status')?.value || '',
        uzytkownik: (document.getElementById('filtr-rezerwacje-uzytkownik')?.value || '').trim().toLowerCase(),
    };
}

async function zaladujLaboratoria() {
    const res = await fetch('/api/laboratoria/');
    wszystkieLaboratoriaRezerwacje = await res.json();
    const select = document.getElementById('laboratorium');
    if (!select) return;
    const currentValue = select.value;
    select.innerHTML = '<option value="">Wybierz laboratorium</option>';
    wszystkieLaboratoriaRezerwacje.forEach(lab => {
        const option = document.createElement('option');
        option.value = lab.id;
        option.textContent = lab.nazwa;
        select.appendChild(option);
    });
    select.value = currentValue;
    await zaladujSprzet();
}

async function zaladujSprzet() {
    const labId = document.getElementById('laboratorium')?.value || '';
    const res = await fetch('/api/sprzet/' + (labId ? '?laboratorium=' + labId : ''));
    wszystkieSprzetyRezerwacje = await res.json();
    const select = document.getElementById('sprzet');
    if (!select) return;
    const currentValue = select.value;
    select.innerHTML = '<option value="">Wybierz sprzęt</option>';
    wszystkieSprzetyRezerwacje.filter(s => !serwisowaneSprzetyWTrakcie.has(String(s.id))).forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = s.nazwa;
        select.appendChild(option);
    });
    select.value = currentValue;
    await pokazDostepnoscSprzetu();
}

async function zaladujSprzetDoEdycji(selectedId) {
    const res = await fetch('/api/sprzet/');
    const data = await res.json();
    const select = document.getElementById('edit-sprzet');
    if (!select) return;
    select.innerHTML = '';
    data.filter(s => String(s.id) === String(selectedId) || !serwisowaneSprzetyWTrakcie.has(String(s.id))).forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = s.nazwa;
        select.appendChild(option);
    });
    select.value = String(selectedId);
    await pokazDostepnoscSprzetu('edit');
}

async function zaladujSprzetyWSerwisieWTrakcie() {
    const res = await fetch('/api/serwis/');
    if (!res.ok) {
        serwisowaneSprzetyWTrakcie = new Set();
        return;
    }
    const data = await res.json();
    serwisowaneSprzetyWTrakcie = new Set(
        data
            .filter(s => statusKey(s.status) === 'w trakcie')
            .map(s => String(s.sprzet))
    );
}

const rezerwacjaForm = document.getElementById('rezerwacja-form');
if (rezerwacjaForm) {
    rezerwacjaForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const sprzet = document.getElementById('sprzet').value;
        const dataRozpoczecia = document.getElementById('data_rozpoczecia').value;
        const dataZakonczenia = document.getElementById('data_zakonczenia').value;
        const res = await fetch('/api/rezerwacje/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                sprzet,
                data_rozpoczecia: new Date(dataRozpoczecia).toISOString(),
                data_zakonczenia: new Date(dataZakonczenia).toISOString(),
                status: 'oczekująca'
            })
        });
        if (res.ok) {
            alert('Rezerwacja złożona!');
            document.getElementById('formularz-rezerwacji').style.display = 'none';
            await pokazRezerwacje();
            odswiezKalendarzJesliDostepny();
        } else {
            const error = await res.json().catch(() => ({}));
            alert(error.error || 'Błąd rezerwacji!');
        }
    });
}

function otworzModalRezerwacji(id, sprzetId, dataRozpoczecia, dataZakonczenia) {
    aktualnieEdyowanaRezerwacja = id;
    
    // Uzupełnij dane formularza
    document.getElementById('edit-rezerwacja-id').value = id;
    document.getElementById('edit-data-rozpoczecia').value = toLocalInputValue(dataRozpoczecia);
    document.getElementById('edit-data-zakonczenia').value = toLocalInputValue(dataZakonczenia);
    zaladujSprzetDoEdycji(sprzetId);
    
    // Pokaż modal i overlay
    const modal = document.getElementById('rezerwacja-modal');
    const overlay = document.getElementById('modal-overlay');
    
    if (overlay) {
        overlay.classList.add('active');
    }
    
    if (modal) {
        modal.classList.add('active');
        // Zablokuj scroll
        document.body.style.overflow = 'hidden';
    }
}

function zamknijModalRezerwacji() {
    aktualnieEdyowanaRezerwacja = null;
    
    const modal = document.getElementById('rezerwacja-modal');
    const overlay = document.getElementById('modal-overlay');
    
    if (modal) {
        modal.classList.remove('active');
    }
    
    if (overlay) {
        overlay.classList.remove('active');
    }
    
    // Przywróć scroll
    document.body.style.overflow = 'auto';
}

async function pokazRezerwacje() {
    const res = await fetch('/api/rezerwacje/');
    wszystkieRezerwacje = await res.json();
    renderujRezerwacje();
}

function renderujRezerwacje() {
    const kontener = document.getElementById('lista-rezerwacji');
    if (!kontener) return;

    const isAdmin = window.currentUserRole === 'admin';
    const filtry = pobierzFiltryRezerwacji();
    const data = wszystkieRezerwacje.filter(r => {
        const statusMatches = !filtry.status || statusKey(r.status) === filtry.status;
        const userText = `${r.uzytkownik_nazwa || ''} ${r.uzytkownik_email || ''} ${r.uzytkownik || ''}`.toLowerCase();
        const userMatches = !isAdmin || !filtry.uzytkownik || userText.includes(filtry.uzytkownik);
        return statusMatches && userMatches;
    });

    if (!data.length) {
        kontener.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">Brak rezerwacji</p>';
        return;
    }

    kontener.innerHTML = '<table><tr>' +
        (isAdmin ? '<th>Użytkownik</th>' : '') +
        '<th>Sprzęt</th><th>Od</th><th>Do</th><th>Status</th><th>Akcje</th></tr>' +
        data.map(r => {
            const key = statusKey(r.status);
            const statusClass = key === 'oczekujaca' ? 'rez-status-oczekujaca' : key === 'aktywna' ? 'rez-status-aktywna' : 'rez-status-anulowana';
            const canEdit = !['zakonczona', 'odrzucona', 'anulowana'].includes(key);
            const editButton = canEdit
                ? `<button class="labflow-btn labflow-btn-primary labflow-btn-sm" onclick="otworzModalRezerwacji(${r.id}, ${r.sprzet}, ${escapeHtml(JSON.stringify(r.data_rozpoczecia || ''))}, ${escapeHtml(JSON.stringify(r.data_zakonczenia || ''))})">Edytuj</button>`
                : '';
            const userCell = isAdmin ? `<td>${escapeHtml(r.uzytkownik_nazwa || r.uzytkownik_email || r.uzytkownik || '')}</td>` : '';
            return `<tr>${userCell}<td>${escapeHtml(r.sprzet_nazwa || '')}</td><td>${formatDateTime(r.data_rozpoczecia)}</td><td>${formatDateTime(r.data_zakonczenia)}</td><td><span class="${statusClass}">${escapeHtml(r.status || '')}</span></td><td><div class="labflow-row-actions">${editButton}</div></td></tr>`;
        }).join('') + '</table>';
}

async function zapisEdytowanejRezerwacji(e) {
    e.preventDefault();
    if (!aktualnieEdyowanaRezerwacja) return;

    const sprzet = document.getElementById('edit-sprzet').value;
    const data_rozpoczecia = document.getElementById('edit-data-rozpoczecia').value;
    const data_zakonczenia = document.getElementById('edit-data-zakonczenia').value;

    try {
        const res = await fetch('/api/rezerwacje/' + aktualnieEdyowanaRezerwacja + '/', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                sprzet,
                data_rozpoczecia: new Date(data_rozpoczecia).toISOString(),
                data_zakonczenia: new Date(data_zakonczenia).toISOString()
            })
        });

        if (res.ok) {
            // Zamknij modal
            zamknijModalRezerwacji();
            // Odśwież listę bez pełnego reloadu
            await pokazRezerwacje();
            odswiezKalendarzJesliDostepny();
            // Pokaż powiadomienie o sukcesie
            if (window.showNotification) {
                showNotification('Rezerwacja zapisana pomyślnie', 'success');
            } else {
                alert('Rezerwacja zapisana pomyślnie!');
            }
        } else {
            const error = await res.json().catch(() => ({}));
            const errorMsg = error.error || error.detail || 'Błąd zapisu rezerwacji!';
            if (window.showNotification) {
                showNotification(errorMsg, 'error');
            } else {
                alert(errorMsg);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (window.showNotification) {
            showNotification('Błąd połączenia', 'error');
        } else {
            alert('Błąd połączenia!');
        }
    }
}

async function anulujRezerwacje(id) {
    if (!confirm('Czy na pewno chcesz anulować tę rezerwację?')) return;
    const res = await fetch('/api/rezerwacje/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (res.ok) {
        await pokazRezerwacje();
        odswiezKalendarzJesliDostepny();
    } else {
        alert('Błąd anulowania rezerwacji!');
    }
}

async function anulujRezerwacjeZModyla() {
    if (!aktualnieEdyowanaRezerwacja) return;
    await anulujRezerwacje(aktualnieEdyowanaRezerwacja);
    zamknijModalRezerwacji();
}

// Obsługa laboratorium change
document.getElementById('laboratorium')?.addEventListener('change', zaladujSprzet);
document.getElementById('sprzet')?.addEventListener('change', () => pokazDostepnoscSprzetu());
document.getElementById('data_rozpoczecia')?.addEventListener('input', () => pokazDostepnoscSprzetu());
document.getElementById('data_zakonczenia')?.addEventListener('input', () => pokazDostepnoscSprzetu());
document.getElementById('edit-sprzet')?.addEventListener('change', () => pokazDostepnoscSprzetu('edit'));
document.getElementById('edit-data-rozpoczecia')?.addEventListener('input', () => pokazDostepnoscSprzetu('edit'));
document.getElementById('edit-data-zakonczenia')?.addEventListener('input', () => pokazDostepnoscSprzetu('edit'));

// Obsługa formularza edycji
document.getElementById('rezerwacja-edit-form')?.addEventListener('submit', zapisEdytowanejRezerwacji);
document.getElementById('filtr-rezerwacje-status')?.addEventListener('change', renderujRezerwacje);
document.getElementById('filtr-rezerwacje-uzytkownik')?.addEventListener('input', renderujRezerwacje);

// Obsługa zamknięcia modala po kliknięciu na overlay
document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('rezerwacja-modal');
    const closeBtn = document.querySelector('.labflow-modal-close');
    const closeModalBtn = document.querySelector('.labflow-modal-actions .labflow-btn-secondary');
    
    // Zamknij po kliknięciu na overlay
    if (overlay) {
        overlay.addEventListener('click', zamknijModalRezerwacji);
    }
    
    // Zamknij po kliknięciu X
    if (closeBtn) {
        closeBtn.addEventListener('click', zamknijModalRezerwacji);
    }
    
    // Zamknij po kliknięciu Zamknij
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', zamknijModalRezerwacji);
    }
    
    // Nie zamykaj modala po kliknięciu wewnątrz
    if (modal) {
        modal.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    await zaladujSprzetyWSerwisieWTrakcie();
    await zaladujLaboratoria();
    await pokazRezerwacje();
});
