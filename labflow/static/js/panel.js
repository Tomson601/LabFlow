// Main Panel Script - Panel.html

function showTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    document.getElementById(tab + '-tab').classList.add('active');
    document.getElementById(tab + '-content').classList.add('active');

    if (tab === 'kalendarz') {
        initCalendar();
    }
}

async function fetchEvents(info, successCallback, failureCallback) {
    try {
        console.log("Pobieram dane z API...");

        const response = await fetch('/api/rezerwacje/', {
            credentials: 'include',
            cache: 'no-store'
        });

        console.log("Status:", response.status);

        if (!response.ok) {
            throw new Error("HTTP error " + response.status);
        }

        const data = await response.json();
        console.log("Dane:", data);

        const events = data.map(item => ({
            title: 'Rezerwacja: ' + (item.sprzet_nazwa || item.sprzet),
            start: item.data_rozpoczecia,
            end: item.data_zakonczenia,
            color: getColor(item.status),
            extendedProps: {
                status: item.status
            }
        }));

        console.log("Events:", events);

        successCallback(events);

    } catch (error) {
        console.error("BŁĄD:", error);
        failureCallback(error);
    }
}

function getColor(status) {
    switch (status) {
        case 'aktywna': return '#007bff'; // mocny niebieski
        case 'oczekująca':
        case 'oczekujaca': return '#ffc107'; // mocny żółty
        case 'anulowana': return '#adb5bd'; // szary
        default: return '#999';
    }
}

function initCalendar() {
    const calendarEl = document.getElementById('calendar');

    if (window.calendarInstance) {
        window.calendarInstance.destroy();
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pl',
        firstDay: 1,
        timeZone: 'local',
        height: 500,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        allDaySlot: false,
        buttonText: {
            today: 'Dziś',
            dayGridMonth: 'Miesiąc',
            timeGridWeek: 'Tydzień',
            timeGridDay: 'Dzień'
        },

        events: fetchEvents,

        eventClick: function (info) {
            const ev = info.event;
            alert(
                'Sprzęt: ' + ev.title +
                '\nOd: ' + ev.start.toLocaleString() +
                '\nDo: ' + ev.end.toLocaleString() +
                '\nStatus: ' + (ev.extendedProps.status || 'brak')
            );
        }
    });

    calendar.render();
    window.calendarInstance = calendar;
}

window.onload = function () {
    showTab('kalendarz');
};
