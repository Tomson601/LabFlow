// Panel Uzytkownicy Module - JavaScript

let wszyscyUzytkownicy = [];

function escapeHtmlUzytkownicy(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

async function pokazUzytkownikow() {
    const kontener = document.getElementById('lista-uzytkownikow');
    if (!kontener || window.currentUserRole !== 'admin') return;

    const res = await fetch('/api/uzytkownicy/');
    if (!res.ok) {
        kontener.innerHTML = '<p class="uzytkownicy-empty">Brak uprawnień do listy użytkowników.</p>';
        return;
    }

    wszyscyUzytkownicy = await res.json();
    renderujUzytkownikow();
}

function roleBadgeClass(rola) {
    return `uzytkownik-role uzytkownik-role-${String(rola || '').toLowerCase()}`;
}

function renderujUzytkownikow() {
    const kontener = document.getElementById('lista-uzytkownikow');
    if (!kontener) return;

    if (!wszyscyUzytkownicy.length) {
        kontener.innerHTML = '<p class="uzytkownicy-empty">Brak użytkowników.</p>';
        return;
    }

    kontener.innerHTML = `
        <div class="uzytkownicy-table-wrap">
            <table class="uzytkownicy-table">
                <thead>
                    <tr>
                        <th>Imię</th>
                        <th>Nazwisko</th>
                        <th>Email</th>
                        <th>Rola</th>
                        <th>Akcje</th>
                    </tr>
                </thead>
                <tbody>
                    ${wszyscyUzytkownicy.map(u => {
                        const isCurrentUser = String(u.id) === String(window.currentUserId);
                        const deleteButton = isCurrentUser
                            ? '<span class="uzytkownik-current">Twoje konto</span>'
                            : `<button class="labflow-btn labflow-btn-danger labflow-btn-sm" onclick="usunUzytkownika(${u.id})">Usuń</button>`;
                        const rolaCell = isCurrentUser
                            ? `<span class="${roleBadgeClass(u.rola)}">${escapeHtmlUzytkownicy(u.rola || '')}</span>`
                            : `<select class="labflow-inline-select uzytkownik-role-select" onchange="zmienUzytkownika(${u.id}, 'rola', this.value)">
                                    ${['student', 'pracownik', 'admin'].map(rola => `<option value="${rola}"${u.rola === rola ? ' selected' : ''}>${rola}</option>`).join('')}
                                </select>`;

                        return `<tr>
                            <td><input class="labflow-inline-input" value="${escapeHtmlUzytkownicy(u.imie || '')}" onchange="zmienUzytkownika(${u.id}, 'imie', this.value)"></td>
                            <td><input class="labflow-inline-input" value="${escapeHtmlUzytkownicy(u.nazwisko || '')}" onchange="zmienUzytkownika(${u.id}, 'nazwisko', this.value)"></td>
                            <td><span class="uzytkownik-email">${escapeHtmlUzytkownicy(u.email || '')}</span></td>
                            <td>${rolaCell}</td>
                            <td>${deleteButton}</td>
                        </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function zmienUzytkownika(id, pole, wartosc) {
    const res = await fetch('/api/uzytkownicy/' + id + '/', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ [pole]: wartosc })
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert(data.error || 'Błąd zapisu użytkownika!');
        await pokazUzytkownikow();
    } else {
        await pokazUzytkownikow();
    }
}

async function usunUzytkownika(id) {
    if (!confirm('Na pewno usunąć użytkownika?')) return;
    const res = await fetch('/api/uzytkownicy/' + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });

    if (res.ok) {
        await pokazUzytkownikow();
    } else {
        const data = await res.json().catch(() => ({}));
        alert(data.error || 'Błąd usuwania użytkownika!');
    }
}

document.addEventListener('DOMContentLoaded', pokazUzytkownikow);
