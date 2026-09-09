// Formatowanie i prezentacja kwot po stronie klienta.
//
// Pakiet jest celowo pusty. Powstał przed pierwszym konsumentem na wyraźną
// decyzję właściciela projektu — rekomendacja brzmiała odwrotnie.
//
// Zakres, gdy przyjdzie czas: wyłącznie prezentacja — formatowanie liczby
// całkowitej groszy na napis w walucie, zgodnie z lokalizacją. Arytmetyka
// pieniędzy nie należy tutaj. Kwota do zapłaty, podatek i podział rabatu na
// pozycje liczone są wyłącznie na backendzie, bo frontend nie może być źródłem
// prawdy o tym, ile klient płaci.
//
// Reprezentacja: liczba całkowita w najmniejszej jednostce waluty plus jawny
// kod waluty — patrz docs/adr/0009-kwoty-jako-liczby-calkowite.md

export {};
