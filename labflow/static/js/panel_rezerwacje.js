// Panel Rezerwacje Module - JavaScript

let wszystkieLaboratoriaRezerwacje = [];
let wszystkieSprzetyRezerwacje = [];
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
    return value.replace('T', ' ').slice(0, 16);
}

function toLocalInputValue(value) {
    if (!value) return '';
    const date = new Date(value);
    const offset = date.getTimezoneOffset();
    return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 16);
}

function odswiezKalendarzJesliDostepny() {
    if (window.calendarInstance && typeof window.calendarInstance.refetchEvents === 'function') {
        window.calendarInstance.refetchEvents();
    }
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
    wszystkieSprzetyRezerwacje.forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = s.nazwa;
        select.appendChild(option);
    });
    select.value = currentValue;
}

async function zaladujSprzetDoEdycji(selectedId) {
    const res = await fetch('/api/sprzet/');
    const data = await res.json();
    const select = document.getElementById('edit-sprzet');
    if (!select) return;
    select.innerHTML = '';
    data.forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = s.nazwa;
        select.appendChild(option);
    });
    select.value = String(selectedId);
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

function otworzModalRezerwacji(id, sprzetId, sprzetNazwa, dataRozpoczecia, dataZakonczenia) {
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
    const data = await res.json();
    const kontener = document.getElementById('lista-rezerwacji');
    if (!kontener) return;

    kontener.innerHTML = '<table><tr><th>Sprzęt</th><th>Od</th><th>Do</th><th>Status</th><th>Akcje</th></tr>' +
        data.map(r => {
            const statusClass = r.status === 'oczekująca' ? 'rez-status-oczekujaca' : r.status === 'aktywna' ? 'rez-status-aktywna' : 'rez-status-anulowana';
            const editButton = `<button class="labflow-btn labflow-btn-primary labflow-btn-sm" onclick="otworzModalRezerwacji(${r.id}, ${r.sprzet}, ${escapeHtml(JSON.stringify(r.sprzet_nazwa || ''))}, ${escapeHtml(JSON.stringify(r.data_rozpoczecia || ''))}, ${escapeHtml(JSON.stringify(r.data_zakonczenia || ''))})">Edytuj</button>`;
            return `<tr><td>${escapeHtml(r.sprzet_nazwa || '')}</td><td>${formatDateTime(r.data_rozpoczecia)}</td><td>${formatDateTime(r.data_zakonczenia)}</td><td><span class="${statusClass}">${escapeHtml(r.status || '')}</span></td><td><div class="labflow-row-actions">${editButton}</div></td></tr>`;
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

// Obsługa formularza edycji
document.getElementById('rezerwacja-edit-form')?.addEventListener('submit', zapisEdytowanejRezerwacji);

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
    await zaladujLaboratoria();
    await pokazRezerwacje();
});
