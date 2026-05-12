// Panel Laboratoria Module - JavaScript

// Obsługa formularza dodawania laboratorium

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
            alert('Laboratorium dodane!');
            document.getElementById('formularz-laboratorium').style.display = 'none';
            pokazLaboratoria();
        } else {
            alert('Błąd dodawania laboratorium!');
        }
    });
}

// Wyświetlanie listy laboratoriów
async function pokazLaboratoria() {
    const res = await fetch('/api/laboratoria/');
    const data = await res.json();
    const kontener = document.getElementById('lista-laboratoriow');
    // Sprawdź uprawnienia użytkownika (rola przekazana przez Django do window.currentUserRole)
    const userRole = window.currentUserRole || 'uzytkownik';
    let html = '<table><tr><th>Nazwa</th><th>Lokalizacja</th><th>Opis</th>';
    if (userRole === 'admin' || userRole === 'pracownik' || userRole === 'superuser') html += '<th>Akcje</th>';
    html += '</tr>';
    html += data.map(lab => {
        if (userRole === 'admin' || userRole === 'pracownik' || userRole === 'superuser') {
            return `<tr><td>${lab.nazwa}</td><td><input value="${lab.lokalizacja}" onchange="zmienLokalizacje(${lab.id}, this.value)"></td><td><input value="${lab.opis || ''}" onchange="zmienOpis(${lab.id}, this.value)"></td><td><button onclick="usunLaboratorium(${lab.id})">Usuń</button></td></tr>`;
        } else {
            return `<tr><td>${lab.nazwa}</td><td>${lab.lokalizacja}</td><td>${lab.opis || ''}</td></tr>`;
        }
    }).join('');
    html += '</table>';
    kontener.innerHTML = html;
}

// Usuwanie laboratorium
async function usunLaboratorium(id) {
    if (!confirm('Na pewno usunąć laboratorium?')) return;
    const res = await fetch('/api/laboratoria/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (res.ok) {
        pokazLaboratoria();
    } else {
        alert('Błąd usuwania!');
    }
}

// Zmiana lokalizacji laboratorium
async function zmienLokalizacje(id, lokalizacja) {
    const res = await fetch('/api/laboratoria/' + id + '/', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ lokalizacja })
    });
    if (!res.ok) {
        alert('Błąd zmiany lokalizacji!');
        pokazLaboratoria();
    }
}

// Zmiana opisu laboratorium
async function zmienOpis(id, opis) {
    const res = await fetch('/api/laboratoria/' + id + '/', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ opis })
    });
    if (!res.ok) {
        alert('Błąd zmiany opisu!');
        pokazLaboratoria();
    }
}

// Automatyczne ładowanie laboratoriów po załadowaniu strony
document.addEventListener('DOMContentLoaded', pokazLaboratoria);

window.addEventListener('DOMContentLoaded', () => {
    pokazLaboratoria();
});
