// Panel Serwis Module - JavaScript

// Załaduj sprzęt do formularza serwisowego
async function zaladujSprzetSerwis() {
    const res = await fetch('/api/sprzet/');
    const data = await res.json();
    const select = document.getElementById('sprzet-serwis');
    select.innerHTML = '';
    data.forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = s.nazwa;
        select.appendChild(option);
    });
}

// Obsługa formularza dodawania zgłoszenia serwisowego
document.getElementById('serwis-form').addEventListener('submit', async function(e) {
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
        pokazSerwis();
    } else {
        alert('Błąd dodawania zgłoszenia!');
    }
});

// Wyświetlanie listy zgłoszeń serwisowych
async function pokazSerwis() {
    const res = await fetch('/api/serwis/');
    const data = await res.json();
    const kontener = document.getElementById('lista-serwis');
    kontener.innerHTML = '<table><tr><th>Sprzęt</th><th>Data zgłoszenia</th><th>Opis</th><th>Status</th><th>Akcje</th></tr>' +
        data.map(s => `<tr><td>${s.sprzet}</td><td>${s.data_zgloszenia ? s.data_zgloszenia.replace('T',' ').slice(0,16) : ''}</td><td>${s.opis}</td><td><select onchange="zmienStatusSerwis(${s.id}, this.value)">${['nowe','w trakcie','zakończone'].map(opt => `<option value="${opt}"${s.status===opt?' selected':''}>${opt}</option>`).join('')}</select></td><td><button onclick="usunSerwis(${s.id})">Usuń</button></td></tr>`).join('') + '</table>';
}

// Usuwanie zgłoszenia serwisowego
async function usunSerwis(id) {
    if (!confirm('Na pewno usunąć zgłoszenie?')) return;
    const res = await fetch('/api/serwis/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (res.ok) {
        pokazSerwis();
    } else {
        alert('Błąd usuwania!');
    }
}

// Zmiana statusu zgłoszenia serwisowego
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
        pokazSerwis();
    }
}

window.addEventListener('DOMContentLoaded', () => {
    zaladujSprzetSerwis();
    pokazSerwis();
});
