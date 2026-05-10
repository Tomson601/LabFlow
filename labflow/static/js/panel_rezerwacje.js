// Panel Rezerwacje Module - JavaScript

// Załaduj laboratoria i sprzęt do formularza
async function zaladujLaboratoria() {
    const res = await fetch('/api/laboratoria/');
    const data = await res.json();
    const select = document.getElementById('laboratorium');
    select.innerHTML = '';
    data.forEach(lab => {
        const option = document.createElement('option');
        option.value = lab.id;
        option.textContent = lab.nazwa;
        select.appendChild(option);
    });
    zaladujSprzet();
}

async function zaladujSprzet() {
    const labId = document.getElementById('laboratorium').value;
    const res = await fetch('/api/sprzet/?laboratorium=' + labId);
    const data = await res.json();
    const select = document.getElementById('sprzet');
    select.innerHTML = '';
    data.forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = s.nazwa;
        select.appendChild(option);
    });
}

document.getElementById('laboratorium').addEventListener('change', zaladujSprzet);

// Obsługa formularza rezerwacji
document.getElementById('rezerwacja-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const sprzet = document.getElementById('sprzet').value;
    // Zamiana na UTC ISO string
    function toUTC(val) {
        if (!val) return null;
        // val: "2026-05-05T12:00"
        const d = new Date(val);
        return d.toISOString();
    }
    const data_rozpoczecia = toUTC(document.getElementById('data_rozpoczecia').value);
    const data_zakonczenia = toUTC(document.getElementById('data_zakonczenia').value);
    const res = await fetch('/api/rezerwacje/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            sprzet: sprzet,
            data_rozpoczecia: data_rozpoczecia,
            data_zakonczenia: data_zakonczenia,
            status: 'oczekująca'
        })
    });
    if (res.ok) {
        alert('Rezerwacja złożona!');
        document.getElementById('formularz-rezerwacji').style.display = 'none';
        pokazRezerwacje();
    } else {
        alert('Błąd rezerwacji!');
    }
});

// Wyświetlanie listy rezerwacji
async function pokazRezerwacje() {
    const res = await fetch('/api/rezerwacje/');
    const data = await res.json();
    const kontener = document.getElementById('lista-rezerwacji');
    const userId = window.currentUserId;
    kontener.innerHTML = '<table><tr><th>Sprzęt</th><th>Od</th><th>Do</th><th>Status</th><th>Akcje</th></tr>' +
        data.map(r => {
            let akcje = '';
            if (userId && Number(r.uzytkownik) === Number(userId)) {
                akcje = `<button onclick="anulujRezerwacje(${r.id})">Anuluj</button>`;
            }
            return `<tr><td>${r.sprzet_nazwa}</td><td>${r.data_rozpoczecia ? r.data_rozpoczecia.replace('T',' ').slice(0,16) : ''}</td><td>${r.data_zakonczenia ? r.data_zakonczenia.replace('T',' ').slice(0,16) : ''}</td><td>${r.status}</td><td>${akcje}</td></tr>`;
        }).join('') + '</table>';

}

// Anulowanie rezerwacji
async function anulujRezerwacje(id) {
    if (!confirm('Czy na pewno chcesz anulować tę rezerwację?')) return;
    const res = await fetch('/api/rezerwacje/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (res.ok) {
        pokazRezerwacje();
    } else {
        alert('Błąd anulowania rezerwacji!');
    }
}

window.addEventListener('DOMContentLoaded', () => {
    zaladujLaboratoria();
    pokazRezerwacje();
});
