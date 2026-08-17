# rxjs-lab

Projekt do planu „Strumień 14 dni" — nauka RxJS i NgRx.

## Stack (celowo dobrany, stabilna para)

- **Angular 21** + **NgRx 21** (store, effects, entity, signals, operators, store-devtools)
- **RxJS 7.8** — linia produkcyjna
- **Vitest** — domyślny test runner Angulara 21 (testy marmurkowe z dnia 7 działają tu bez przeglądarki)
- **json-server 1.0** — lokalne API bez internetu

Wymagany Node: `^20.19.0 || ^22.12.0 || >=24.0.0` — sprawdź `node -v` przed lotem.

## Komendy

```bash
npm start            # aplikacja na http://localhost:4200
npm run api          # mock API na http://localhost:3000 (repos, favorites)
npm test             # testy (vitest, jednorazowo: npm test -- --watch=false)
```

## Mock API (`db.json`)

- `GET /repos` — lista 30 repozytoriów
- `GET /repos?name=rx` — filtrowanie (wyszukiwarka, dzień 6)
- `GET /repos?_page=1&_per_page=10` — stronicowanie (infinite scroll, dzień 4)
- `PATCH /repos/:id` — gwiazdka / odgwiazdkowanie (optymistyczne aktualizacje, dzień 11)
- `GET /favorites`, `POST /favorites` — ulubione (kolejka zapisów, concatMap)

Symulacja wolnego/wadliwego API: json-server 1.0 nie ma już `--delay`, więc
opóźnienia i błędy 500 najlepiej dodać po stronie Angulara interceptorem —
to zresztą ćwiczenie samo w sobie (dzień 5).

## Skąd ten projekt

Utworzony w dniu zerowym planu: `ng new` + pakiety NgRx + json-server,
build i testy przeszły na czysto. Cache npm jest kompletny — `npm ci`
i praca offline nie powinny niczego dociągać.
