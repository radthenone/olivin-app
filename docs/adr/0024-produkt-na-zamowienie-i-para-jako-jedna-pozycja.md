# Produkt na zamówienie: bez stanu magazynowego, para obrączek jako jedna pozycja

Obrączki ślubne są wytwarzane po złożeniu zamówienia: nie mają stanu
magazynowego ani rezerwacji, mają czas realizacji, a ich wariant opisują
parametry wykonania. Zamówienie z takim produktem przechodzi przez dodatkowy
etap `in_production`, a przesyłka powstaje dopiero po nim. Para obrączek to
jedna pozycja koszyka z dwoma egzemplarzami o osobnych rozmiarach — świadome
odstępstwo od zasady, że pozycja to jeden wariant, bo klient kupuje parę jako
całość i tak samo ją zwraca. Konfigurator z wyceną na żywo odrzucony jako
przedwczesny. Produkt magazynowy nigdy nie staje się produktem na zamówienie po
wyczerpaniu stanu — to dwie rozłączne klasy.

## Consequences

Grawer ([ADR 0018](0018-grawer-jako-opcja-wylaczajaca-zwrot.md)) i produkt na
zamówienie wyłączają ustawowe prawo odstąpienia — oba czynią wyrób
zindywidualizowanym.
