// Panel Sprzęt Module - JavaScript

// Załaduj laboratoria do formularza sprzętu
async function zaladujLaboratoriaSprzet() {
    const res = await fetch('/api/laboratoria/');
    const data = await res.json();
    const select = document.getElementById('laboratorium-sprzet');
    select.innerHTML = '';
    data.forEach(lab => {
        const option = document.createElement('option');
        option.value = lab.id;
        option.textContent = lab.nazwa;
        select.appendChild(option);
    });
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
async function pokazSprzet() {
    const res = await fetch('/api/sprzet/');
    const data = await res.json();
    const kontener = document.getElementById('lista-sprzetu');
    // Sprawdź uprawnienia użytkownika (rola przekazana przez Django do window.currentUserRole)
    const userRole = window.currentUserRole || 'uzytkownik';
    kontener.innerHTML = '<table><tr><th>Nazwa</th><th>Kategoria</th><th>Status</th><th>Laboratorium</th><th>Akcje</th></tr>' +
        data.map(s => {
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
});
